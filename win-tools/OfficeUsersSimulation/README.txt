• In the 'Debug' folder you can run the file "OfficeUsersSimulation_C.exe".

• In the 'publish' folder you can find the installation file. 
You do NOT need to isntall the software, I just include the files in case you want them.


~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Version 2:
	~ bug fix: 		- continuously loading defaults (or last) values
				- could start empty files creation, even with no "use word/excel" selection
				- while empty files running "use word/excel" could be changed
				- if word/excel operations finish before "empty files" creation, button remains at "STOP" state
					(restoreAfterRun() do not run before empty files creation is also completed)

	~ add:			- "autoDelete" option deletes also "empty files" folder (if user doesn't choose to open 
					the folder containing the files)

	~ known issues:		- at manual STOP (or Empty creation stop), excel instance remains (sometimes)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
				