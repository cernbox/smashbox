import smashbox.configgen.processors as processors

class Generator(object):
    '''
    Class to generate configuration files.

    You need to set a processor chain in order to process the dict-like object
    and write it into a file. If no processor is set, it will write the same object

    Result may vary depending the processor chain being used
    '''
    def __init__(self, processor_list = None):
        '''
        Initialize the object with the processor chain set, or with an empty chain
        if None
        '''
        self.processor_list = [] if processor_list == None else processor_list

    def insert_processor(self, i, processor):
        '''
        Insert a new processor in the "i" position
        Check list.insert for details
        '''
        self.processor_list.insert(i, processor)

    def append_processor(self, processor):
        '''
        Append the processor to the end of the chain
        '''
        self.processor_list.append(processor)

    def get_processor_list(self):
        '''
        Get the processor list / chain
        '''
        return self.processor_list

    def get_processor_by_name(self, name):
        '''
        Get the processor by name or None if it's not found
        '''
        for p in self.processor_list:
            if p.get_name() == name:
                return p

    def process_dict(self, local_dict):
        '''
        Process the dictionary. It will go through all the process chain and it will be
        returned after that.
        '''
        for p in self.processor_list:
            local_dict = p.do_process(local_dict)
        return local_dict

    def write_dict(self, output_file, local_dict):
        '''
        Write the dictionary into a file. It will be readable by using the execfile
        function, which should be the same or similar format that the smashbox.conf.template
        file has, and MUST be a valid smashbox.conf file
        '''
        with open(output_file, 'w') as f:
            for key in local_dict:
                f.write('%s = %s\n' % (key, repr(local_dict[key])))

    def generate_new_config(self, input_file, output_file):
        '''
        Generate a new configuration file from the input_file. The input file should be
        similar to the smashbox.conf.template. The processor chain must be set before
        calling this function
        '''
        input_globals = {}
        input_locals = {}
        execfile(input_file, input_globals, input_locals)

        input_locals = self.process_dict(input_locals)
        self.write_dict(output_file, input_locals)

    def set_processors_from_data(self, processor_data):
        '''
        Set the processor chain based on the data passed as parameter. Check the
        _configgen variable in the smashbox.conf.template for working data

        The processor_data should be a dictionary-like. Due to the order of the processor
        matters, an OrderedDict is recommended.
        The keys of the dictionary are
        the class name of the processor that will be used (from the
        smashbox.configgen.processors module). Currently there are only 4 processors available.
        The value for the key should also be a dictionary to initialize the processor. Only
        one parameter will be passed, that's why a dictionary is recommended, although
        what you must pass depends on the specific processor.
        '''
        for key in processor_data:
            if hasattr(processors, key):
                processor_class = getattr(processors, key)
                if not issubclass(processor_class, processors.BasicProcessor):
                    continue
                values = processor_data[key]
                processor = processor_class(values)
                self.append_processor(processor)
            else:
                pass

    def process_data_to_file(self, data, output_file):
        '''
        Process the data passed as parameter through the chain and write the result
        to the file
        '''
        data_to_output = self.process_dict(data)
        self.write_dict(output_file, data_to_output)

