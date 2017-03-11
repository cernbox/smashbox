| Test#         | Short/Long    |  Action             |  Test            |  Expected Result               | Comment | Test result |
| ------------- |:-------------:| -----------------:|:-----------------|:-------------------------------|:----------------|:----------|
| 1.1             | Short         | Login             | Case sensitive   | It is possible to login        | [login.feature](https://github.com/owncloud/acceptance-testing/blob/master/features/login.feature) | |
| 1.2             | Short         | Login             | Wrong credentials| An alert message is displayed  | | |
| 1.3             | Short         | Login             | Change password|   | Maybe in the future| |
| 1.5             | Short         | Login             |Change the storage using the different options | The storage is changed | |
| 2.1             | Short         | Upload            | Upload a file     | File gets uploaded to OC        | | |
| 2.2             | Short         | Upload            | Drag and drop     | File gets uploaded to OC        | | |
| 2.3             | Short         | Upload            | Drag and drop     | Folders gets uploaded to OC        | | |
| 2.4             | Short         | Upload            | Upload more than 1 | Files get uploaded to OC       | | |
| 2.5             | Short         | Upload            | Upload a file that already exists | An alert message is displayed | | |
| 2.6              | Short         | Upload            | Upload a file that already exists, select suggest name |The file gets upload with a new name | select suggest ?| |
| 2.7             | Short         | Upload            | Upload a file that already exists, select cancel | The file is not upload | | |
| 2.8            | Short         | Upload            | Upload a file taht already exists, select replace | The file available on the server is replaced with the new one | | |
| 2.9            | Short         | Upload            | File size        | After uploading a new file, it size is shown on MB | | |
| 2.10            | Short         | Upload            | Files whose names include special characters | Files get uploaded | | |
| 2.11           | Short          | Upload            | Upload files to a subfolder | Files get uploaded | | |
| 2.12           | Short          | Upload            | Progress bar is visible | When uploading files, progress bar is visible | | |
| 2.13           | Short          | Upload            | Upload finishes     | When an upload finishes, the loading icon disappears | | |
| 2.14           | Short          | Upload            | Create a folder     | It is automatically displayed | | |
| 2.15           | Short          | Upload            | Cancel upload       | The upload stops              | | |
| 2.16           | Short          | Upload            | Cancel the creation of a new file/folder | By clicking the outside the submenu, the file/folder is not created | | |
| 2.17           | Short          | Upload             | Upload a single document with a long name (100 characters) | File gets uploaded | | |
| 2.18           | Short          | Upload            | Create a folder with a long name (100 characters) | Folder is created | | |
| 2.19           | Short          | Upload            | Create a folder whose name is Shared | Not possible, an alert message is shown | | |
| 2.20           | Short          | Upload            | Having reached the maximum storage capacity, upload a file | An alert message is shown | Create a new account with a small capacity| |
| 2.21           | Short          | Upload            | Upload a file whose size is larger than the maximum available size | An alert message is shown | Create a new account with a small capacity| |
| 2.22           | Short           | Upload          |  Set maximum upload to 1 Gb | upload a file of 1 Gb| Create a new account| |
| 2.23           | Short           | Upload        | Lots of documents | Upload 100 documents, 1 G | | |
| 2.24           | Short           | Upload        | Create a folder whose name is the same as one document |Create a file whose name is "a", Create a folder whose is "a", The folder is created | | |
| 7.1        | Short              | Preview         | Preview png | The file is displayed  | maybe in the future| |
| 7.2        | Short              | Preview         | Preview gif | The file is displayed  | maybe in the future| |
| 7.3        | Short              | Preview         | Preview pdf | The file is displayed  | maybe in the future| |
| 7.4        | Short              | Preview         | Preview txt | The file is displayed   | | |
| 7.5        | Short              | Preview         | Preview html | The file is displayed   | | |
| 7.6        | Short              | Share           |Share a file with a colleague(s)  |  Colleague(s) has access to the file  | | |
| 8.1        | Short              | Share           |Share a folder with a colleague(s)  |  Colleague(s) has access to the folder including any subfolder and files  | | |
| 8.2        | Short              | Share           | Having a shared folder we include a new file on it | Colleague can access to it   | | |
| 8.3        | Short              | Share           | Having a shared folder we delete it | The folder is deleted too   | | |
| 8.4        | Short              | Share           | Having a shared file, we delete it  |  The file is deleted | | |
| 8.5        | Short              | Share            | Having a shared folder, from the other user we select to to stop sharing it  | The folder is not shared   | | |
| 8.6        | Short              | Share            |  Shared a folder whose name includes special characters | The folder is shared   | | |
| 8.7        | Short              | Share            | Shared a folder and set it as not "shared"  | Resharing is not possible    | | |
| 8.8        | Short              | Share            | Shared a folder without edit privileges. Try to modify a txt stored on it  | Not possible, to include changes   | | |
| 8.9        | Short              | Share            | Shared a large file, 1Gb  | It´s shared   | | |
| 8.10        | Short              | Share            |  Having shared file, with privileges, we modified from user | Changes are reflected in all users   | | |
| 8.11        | Short              | Share            |  Having shared file, with privileges, we modified from other user but the owner | Changes are reflected   | | |
| 8.12        | Short              | Share            | Having a shared file, we modified it from two clients at the same time   | In one of them it is not possible to save changes   | | |
| 8.13        | Short              | Share            |  We select to share a folder with a link, after receiving the mail link, we access to OC and select to download the folder    |The folder gets downloaded | | |
| 8.14        | Short              | Share            | We select to share a file with a link, after receiving the mail link, we access to OC and select to download the folder  |  The file gets downloaded  | | |
| 8.15        | Short              | Share            |  The shared icon is displayed although we log out | The icon is displayed    | | |
| 8.16        | Short              | Share            |  The shared icon is displayed in all shared files | Not only the folder shows the icon but also all files stored on it   | | |
| 8.17        | Short              | Share            | We rename a shared folder  | It keeps being a shared folder  | | |
| 8.18        | Short              | Share            |  Having edit privileges, it is possible to modify a file |  File gets updated  | | |
| 8.19        | Short              | Share            | Shared a folder with a group  | Folder is visible for all members of the group   | | |
| 8.20        | Short              | Share            | Shared a folder without privileges  | It is not possible to upload nor create new folder or files   | | |
| 8.21        | Short              | Share            | Shared a link if "allow links" is not enabled  | It should not be possible| | |
| 8.22        | Short              | Share            | Message when "allow links" is not enabled | If "allow files" is not enabled, an alert message is shown, this message should include the name of the file| | |
| 8.23        | Short              | Share            | It is possible to share something previously shared via link while "allow links" is not enabled | Select to share with link a file that has been previously shared with a link| | |
| 8.24        | Short              | Share            | Error by sharing a file with link a non-admin user from Chrome and opening the link on FF| It is possible to download the share file| | |
| 8.25        | Short              | Share            |Move files into a shared folder| Files are uploaded| | |
| 8.26        | Short              | Share            |Message when resharing is not allowed| Select to share the folder, the dialogue is shown "Resharing is not allowed"| | |
| 8.27        | Short              | Share            |Set not allowed resharing on admin| Check that by default the share option is not set when sharing a file| | |
| 8.28        | Short              | Share            |When it is not allowed resharing, it should not be possible to check share| Check the privileges, it is possible to checked the option share. However, this check is not saved.| | |
| 8.29        | Short              | Share            |Rename a shared folder|The folder is still shared | | |
| 8.30        | Short              | Share            |Group names are shown when selecting share to |The group names should not be hidden, although the mouse is over them| | |
| 8.31        | Short              | Share            | Access to a shared subfolder|On one user create the folders a>a1, and select to share it with another user, user2. Access as user2, to the Shared folder, and to a and a1| | |
| 14.1        | Short              | Anonymous upload            | Upload file, photo, video,... | Files get upload to owncloud | It is not possible to upload as Anonymous| Why no preview as an Anonymous user|
| 14.8        | Short              | Anonymous upload            | File size |  It is shown the file size on MB| | |
| 14.9        | Short              | Anonymous upload            |  Upload a 1GB file| An alerert message should be shown  | | |
| 14.10        | Short              | Anonymous upload            |  Upload a file whose size is larger than the maximum available size| An alerert message is shown "Not enought storage available" | Max size| |
| 14.11        | Short              | Anonymous upload            | Shared a file and enable "Allow public upload" | You shouldnt enable "Allow public upload" in a file  | | |  
| 14.12        | Short              | Anonymous upload            | Upload a file using "Password protect"   |  Files get upload | | |
| 14.13       | Short              | Anonymous upload            | Check the uploads are visible from the desktop client |  The files are visible from the desktop client| | |  
| 14.14        | Short              | Anonymous upload            |  Shared a file and enable "Allow public upload" via email| The file is shared | | |