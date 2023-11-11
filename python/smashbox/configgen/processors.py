from collections import OrderedDict
import sys

class ProcessorException(Exception):
    '''
    Exception that will raise from processor classes
    '''
    KEY_DATA_MISSING = 1
    REQUIRED_KEY_MISSING = 2
    UNKNOWN_CONVERSION = 3
    def __init__(self, error_code, message):
        super(ProcessorException, self).__init__(message)
        self.error_code = error_code

def convert_string_to_type(string, totype):
    '''
    Simple type converter based on our rules. Any processor class from this module or
    any piece of code which might use this module (dictionaries for the OverwritterProcessor)
    should use this function to convert types
    '''
    if totype == 'int':
        return int(string)
    elif totype == 'float':
        return float(string)
    elif totype == 'None':
        return None if string == 'None' else string
    elif totype == 'bool':
        return string == 'True'
    elif totype == 'list':
        return string.split(',')
    raise ProcessorException(ProcessorException.UNKNOWN_CONVERSION, 'unknown conversion requested')

class BasicProcessor(object):
    '''
    Basic processor class. All processor should inherit from this class

    The class provides an observer mechanism to notify changes. Code can be hooked
    using this system into the processor. Available notifications will depend on
    the specific processor as well as when the notification is send

    This class also provide a simple way to obtain a default name for the processor
    (implementations shouldn't need to change this, but it's possible), as well as
    a simple way to ask for keys (looks enough for now).
    '''
    def __init__(self, params):
        self.observer_dict = OrderedDict()
        self.params = params

    def register_observer(self, name, observer):
        '''
        Register an observer with the appropiated name. The observer MUST have a "notify_me"
        method accepting 3 parameters: the processor name, the event type (defined in each
        processor) and the message (depending on the event type)
        '''
        self.observer_dict[name] = observer

    def unregister_observer(self, name):
        '''
        Unregister the observer with the specified name
        '''
        del self.observer_dict[name]

    def _notify_observer(self, name, event_type, message):
        '''
        This is an internal function for the class and shouldn't be call from outside

        Notify the specified observer (by name) with the corresponding event type and message
        '''
        self.observer_dict[name].notify_me(self.get_name(), event_type, message)

    def _notify_all(self, event_type, message):
        '''
        This is an internal function for the class and shouldn't be call from outside

        Notify all observers with the corresponding event type and message
        '''
        for key in self.observer_dict:
            self.observer_dict[key].notify_me(self.get_name(), event_type, message)

    def get_name(self):
        '''
        Convenient function to get the name of the processor. The default is the class name
        '''
        return self.__class__.__name__

    def do_process(self, config_dict):
        '''
        This method MUST be implemented in each subclass
        '''
        raise NotImplementedError('method not implemented')

    def ask_for_key(self, key_name, help_text=None, default_value=None):
        '''
        Ask for a key value interactively and return the user's input
        '''
        if default_value is None:
            default_value = ''

        if help_text is None:
            sys.stdout.write('%s [%s] : ' % (key_name, default_value))
        else:
            sys.stdout.write('%s -> %s\n[%s] : ' % (key_name, help_text, default_value))
        sys.stdout.flush()

        input_value = sys.stdin.readline().rstrip()
        if not input_value and default_value is not None:
            return default_value
        else:
            return input_value


class RequiredKeysProcessor(BasicProcessor):
    '''
    Processor to fill required keys. All the keys are defined when this object is created.

    This processor accepts as parameter a dictionary with 2 keys:
    * keylist -> containing info for the required keys
    * ask -> True / False to decide to ask for missing keys or throw an exception

    The keylist info will contain (for now) something like:
    {'keylist' : [{'name': 'the_name_of_the_key',
                  'help_text': 'optional text to show as help',
                  'default': 'the default value if the user doesn't input anything',
                  'type': 'type conversion if needed (check convert_string_to_type function'},
                 {......}]}

    Event list:
    * EVENT_PROCESS_INIT when the process starts
    * EVENT_PROCESS_FINISH when the process finish (just before return the result)
    * EVENT_KEY_MODIFIED when a required key is modified
    * EVENT_KEY_ALREADY_SET when a required key is already set and won't be modified
    '''
    EVENT_PROCESS_INIT = 'process_init'
    EVENT_PROCESS_FINISH = 'process_finish'
    EVENT_KEY_MODIFIED = 'key_modified'
    EVENT_KEY_ALREADY_SET = 'key_already_set'

    def set_ask(self, ask):
        '''
        set the "ask" parameter dynamically
        '''
        self.params['ask'] = ask

    def do_process(self, config_dict):
        self._notify_all(self.EVENT_PROCESS_INIT, None)

        for key_data in self.params['keylist']:
            if not 'name' in key_data:
                # check that the key_data contains a name for the key
                raise ProcessorException(ProcessorException.KEY_DATA_MISSING,
                                        'name attribute in the key data is missing')

            real_key = key_data['name']
            placeholder = key_data.get('help_text', None)
            default_value = key_data.get('default', None)

            if real_key in config_dict:
                self._notify_all(self.EVENT_KEY_ALREADY_SET, {'key': real_key, 'value': config_dict[real_key]})
                continue
                # if the key exists jump to the next one

            if self.params['ask']:
                value = self.ask_for_key(real_key, placeholder, default_value)
                if 'type' in key_data:
                    value = convert_string_to_type(value, key_data['type'])
                config_dict[real_key] = value
                self._notify_all(self.EVENT_KEY_MODIFIED, {'key': real_key, 'value': value})
            else:
                if not real_key in config_dict:
                    raise ProcessorException(ProcessorException.REQUIRED_KEY_MISSING,
                                            'required key is missing')

        self._notify_all(self.EVENT_PROCESS_FINISH, None)

        return config_dict

class KeyRemoverProcessor(BasicProcessor):
    '''
    Processor to remove keys. All the keys to be removed are defined when this object is created.

    This processor accepts as parameter a dictionary with 1 key:
    * keylist -> containing a list of keys to be removed

    The keylist info will contain (for now) something like:
    {'keylist' : ('key1', 'key2', 'key3', ....)}

    Event list:
    * EVENT_PROCESS_INIT when the process starts
    * EVENT_PROCESS_FINISH when the process finish (just before return the result)
    * EVENT_KEY_DELETED when a key is deleted
    '''
    EVENT_PROCESS_INIT = 'process_init'
    EVENT_PROCESS_FINISH = 'process_finish'
    EVENT_KEY_DELETED = 'key_deleted'

    def do_process(self, config_dict):
        self._notify_all(self.EVENT_PROCESS_INIT, None)
        for key in self.params['keylist']:
            del config_dict[key]
            self._notify_all(self.EVENT_KEY_DELETED, key)
        self._notify_all(self.EVENT_PROCESS_FINISH, None)
        return config_dict

class SortProcessor(BasicProcessor):
    '''
    Processor to sort keys.

    This processor doesn't require parameters so you can just set the param as None

    Event list:
    * EVENT_PROCESS_INIT when the process starts
    * EVENT_PROCESS_FINISH when the process finish (just before return the result)
    '''
    EVENT_PROCESS_INIT = 'process_init'
    EVENT_PROCESS_FINISH = 'process_finish'

    def do_process(self, config_dict):
        self._notify_all(self.EVENT_PROCESS_INIT, None)
        result = OrderedDict(sorted(config_dict.items(), key=lambda t: t[0]))
        self._notify_all(self.EVENT_PROCESS_FINISH, None)
        return result

class OverwritterProcessor(BasicProcessor):
    '''
    Processor to overwrite keys.

    This processor accepts as parameter a dictionary with 1 key:
    * dict_to_merge -> containing a dictionary to update the configuration

    Event list:
    * EVENT_PROCESS_INIT when the process starts
    * EVENT_PROCESS_FINISH when the process finish (just before return the result)
    * EVENT_BULK_UPDATE after updating the dictionary
    '''
    EVENT_PROCESS_INIT = 'process_init'
    EVENT_PROCESS_FINISH = 'process_finish'
    EVENT_BULK_UPDATE = 'bulk_update'

    def set_dict_to_merge(self, merge_dict):
        '''
        set the "dict_to_merge" parameter dynamically
        '''
        self.params['dict_to_merge'] = merge_dict

    def do_process(self, config_dict):
        self._notify_all(self.EVENT_PROCESS_INIT, None)
        config_dict.update(self.params['dict_to_merge'])
        self._notify_all(self.EVENT_BULK_UPDATE, self.params['dict_to_merge'])
        self._notify_all(self.EVENT_PROCESS_FINISH, None)
        return config_dict
