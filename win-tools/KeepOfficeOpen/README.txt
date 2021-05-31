• In 'Debug' folder you can run the file "KeepItOpen.exe".

• In 'publish' folder you can find the installation file. 
You do NOT need to install the software, I just include the files in case you want them.


Instructions:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Available arguments ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1)	r (or) w			: file in 'read' or 'write' mode
2)	file + <path> 			: path to word OR excel file to keep open
3)	delay1 + <integer[1-3600]> 	: delay in seconds that file will be kept open
4)	delay2 + <integer[0-3600]> 	: extra delay in seconds (ONLY in 'w' mode)
5)	s 				: silent mode - no confirmation asked

1) 	Open the file in either READ (r) or WRITE (w) mode.
	In READ mode, the file will be kept open for as many seconds as defined by
	parameter 'delay1'. Parameter 'delay2' is ignored. 
	Then the file is closed and the software exits.
	
	In WRITE mode, the file opens and stays open for as many seconds as defined 
	by parameter 'delay1'. Then some random Lorem Ipsum text is written.
	Keep in mind that any text inside the file will be OVERWRITTEN!
	If set, additional delay 'delay2' is applied in that point. 
	Then the file is closed and the software exits.

2)	Give the path to the office file that will be kept open. 
	Accepted formats: .doc .docx .xls .xlsx

5)	If this argument is added, the software will not ask for confirmation.
	In case this argument is missing, you will be presented a sum of the arguments
	and will be asked to confirm.

Arguments (1) , (2) & (3) are mandatory. Arguments (4) & (5) can be skipped.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Check "args tests.txt" file for some examples.