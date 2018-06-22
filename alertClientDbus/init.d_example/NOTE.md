# Permissions

Note if you start this AlertR client as a different user than the one the X session is running on, you need to allow this user to access your X session in order to display notifications. For example, if the user the AlertR client is running on is `alertr` and the user you use for your daily usage is `myuser`, then `myuser` has to execute the following command each time she/he logs in:

```bash
xhost +SI:localuser:alertr
```

This allows the user `alertr` to access the X session of `myuser`. In order to automate this, it is best to place this command somewhere that is executed each time the user logs in like the `.xsessionrc` file.