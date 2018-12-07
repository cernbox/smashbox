# Testplan for updating the mobile app

_If you have already installed the test version some of the steps may not be applicable_

1. Make sure you have the current production version of the mobile app installed, you are logged in and it works. 
2. Exercise basic functions with production version
   1. Download/pin some files for download (locally cached)
   2. ...
3. Update to the test version.
5. Check if the previous state is kept
   1. Make sure that you are still logged in after update.
   2. Make sure that cached files in the offline mode are accessible.
6. Perform basic functionality tests:
   1. Browsing of folders. 
      - Traverse a folder tree several levels down.
      - Modify folder (e.g add a new file, rename existing one) via sync client and web interface and see if the browser view is refreshed.
   2. Create a folder.
   3. Upload a file: small file (<1M), big file (>30M).
   4. Download files (small, big).
   5. Rename files and folders.
   6. Take photo using the camera and check if it is uploaded automatically to the server.
7. Logout and check if you can login again.
  
