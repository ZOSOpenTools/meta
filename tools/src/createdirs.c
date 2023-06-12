#define _ISOC99_SOURCE
#include <sys/types.h>
#include <sys/stat.h>
#include <errno.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>

#include "createdirs.h"
#include "zopenio.h"

static int createsubdir(const char* rootdir, const char* subdir) {
  char fulldir[ZOPEN_PATH_MAX+1];
  struct stat stfull = {0};

  if (snprintf(fulldir, ZOPEN_PATH_MAX, "%s/%s", rootdir, subdir) > ZOPEN_PATH_MAX) {
    return ZOPEN_CREATEDIR_DIR_TOO_LONG;
  }
  if (stat(fulldir, &stfull) == -1) {
    if (mkdir(fulldir, S_IRWXU|S_IRGRP|S_IXGRP|S_IROTH|S_IXOTH)) {
      return ZOPEN_CREATEDIR_CREATE_FAILED;
    } else {
      return 0;
    }
  } else {
    return ZOPEN_CREATEDIR_DIR_EXISTS;
  }
}

/*
 * Create the directories needed for a z/OS Open Tools
 * development environment including the root directory
 * passed in.
 *
 * If a directory already exists, it will not be modified,
 * and this will not be considered a 'failure'
 *
 * Returns non-zero if the directories can not be created
 */

int createdirs(const char* rootdir) {
  struct stat stroot = {0};
  const char* subdir[] = { ZOPEN_DEV, ZOPEN_BOOT, ZOPEN_PROD, NULL };
  const char *rootsubdir;
  char dir[ZOPEN_PATH_MAX+1];
  char dirtokbuf[ZOPEN_PATH_MAX+1];
  int rc;
  int i;

  memset(dir, 0x00, sizeof(dir));
  sprintf(dir, "%s", ZOPEN_DIR_DELIMITER);
  strcpy(dirtokbuf, rootdir);
  rootsubdir=strtok(dirtokbuf, ZOPEN_DIR_DELIMITER);

  /* create root directory tree */
  while (rootsubdir != NULL) {
    strcat(dir, rootsubdir);
    if (stat(dir, &stroot) == -1) {
      /* root subdirectory doesn't exist - create it */
      if (rc = createsubdir(dir, "")) {
        if (rc != ZOPEN_CREATEDIR_DIR_EXISTS) {
          fprintf(stderr, "Could not create root subdirectory '%s': %s\n", dir, strerror(errno));
          return rc;
        }
      }
    }
    strcat(dir, ZOPEN_DIR_DELIMITER);
    rootsubdir=strtok(NULL, ZOPEN_DIR_DELIMITER);
  }
   
  /* create predefined subdirectories */
  for (i=0; subdir[i] != NULL; ++i ) {
    if (rc = createsubdir(dir, subdir[i])) {
      if (rc != ZOPEN_CREATEDIR_DIR_EXISTS) {
        fprintf(stderr, "Could not create subdirectory '%s': %s\n", subdir[i], strerror(errno));
        return rc;
      }
    }
  }

  return 0;
}
