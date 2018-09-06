# AlertR

AlertR is a client/server based alarm system and monitoring system which targets developers, tinkers, privacy advocates, and all people that are interested in DIY solutions. Despite the obvious use as a home alarm system, it can also be used to help server administrators to monitor their services (or used in any other cases in which sensors are required). Because of the way it is designed, AlertR can be used in any scenario a sensor with the state `triggered` and `normal` has to be monitored. This can be a sensor for a home security or home automation system, but also computer services like a failing HDD drive in a RAID or the availability of a web server.

The vision for AlertR is to have a single service running that           gathers all the information someone wants (like temperature data, service states, or bank account transfers) and provides the ability to react on them automatically. In addition, it should serve as single point to let the user look up aggregated information of his/her services. All this should be done in such a way that the user is always in control of his/her data and no one besides him/her is able to access them.

The project is well documented in the [Github Wiki](https://github.com/sqall01/alertR/wiki/) and a community page can be found on [reddit](https://www.reddit.com/r/AlertR/).


# Table of Contents
* [Version](#version)
* [Media](#media)
  * [Pictures](#media_pictures)
  * [Videos](#media_videos)
* [Installation](#installation)
* [Update](#update)
* [Further Notes](#further_notes)
* [Supporting AlertR](#supporting_alertr)
* [Bugs and Feedback](#bugs_and_feedback)


# Version
<a name="version"/>

The current stable version of AlertR is 0.5. The development of AlertR is done in the dev-branch. So if you want to see the next features or just check if the project is still alive, please see the commits in the dev-branch. If you want to see what has changed during the releases, you can check the [Changelog File](CHANGELOG.md).


# Media
<a name="media"/>

If you have no idea what AlertR actually is or how you can use it, this section might give you some ideas.


## Pictures
<a name="media_pictures"/>

A picture of a [MagicMirror](https://magicmirror.builders/) showing AlertR system information.

<div align="center">
<img src="docs/magicmirror.jpg" />
</div>
<br />

The following shows a screenshot of the [Android app](https://play.google.com/store/apps/details?id=de.alertr.alertralarmnotification) introduced in version 0.5.

<div align="center">
<img src="docs/screenshot_android_app.png" />
</div>
<br />

A screenshot of the console manager in version 0.4.

<div align="center">
<img src="docs/manager_console_screenshot_v0.4.jpg" />
</div>
<br />

An overview of the infrastructure a basic AlertR setup has.

<div align="center">
<img src="docs/alertR_infrastructure_basic.jpg" />
</div>
<br />

Number of active AlertR installations calculated from participants of the voluntary survey.

<div align="center">
<img src="https://alertr.de/img/graphs/survey_numbers.php" />
</div>
<br />

Number of messages sent by the AlertR push service in the last 12 weeks.

<div align="center">
<img src="https://alertr.de/img/graphs/push_numbers.php" />
</div>
<br />


## Videos
<a name="media_videos"/>

A short preview of the AlertR alarm and monitoring system in version 0.5. It shows the new AlertR Android app that is able to receive push notifications. Please activate the subtitles to see the description of what I am doing and what is happening.

<div align="center">
<a href="https://www.youtube.com/watch?feature=player_embedded&v=gafnnETwNYA&yt:cc=on" target="_blank">
<img src="https://img.youtube.com/vi/gafnnETwNYA/0.jpg" width="640" height="480" border="10" />
</a>
</div>
<br />

Part of one release was a rule engine, which allows you to set up rules that must be satisfied before an alarm is triggered. Again, the subtitles have to be activated in order to understand what is happening.

<div align="center">
<a href="https://www.youtube.com/watch?feature=player_embedded&v=iP3uPX41QEg&yt:cc=on" target="_blank">
<img src="https://img.youtube.com/vi/iP3uPX41QEg/0.jpg" width="640" height="480" border="10" />
</a>
</div>
<br />

The next video was published in December 2014 and shows version 0.2 of AlertR. It demonstrates the D-Bus and Kodi (aka XBMC) notification capabilities. Again, the subtitles have to be activated in order to understand what is happening.

<div align="center">
<a href="https://www.youtube.com/watch?feature=player_embedded&v=r7caH_UzKms&yt:cc=on" target="_blank">
<img src="https://img.youtube.com/vi/r7caH_UzKms/0.jpg" width="640" height="480" border="10" />
</a>
</div>
<br />

The following video is a short introduction video of AlertR as a home alarm system. It was the first video showing AlertR. The subtitles have to be activated in order to understand what is happening.

<div align="center">
<a href="https://www.youtube.com/watch?feature=player_embedded&v=TxhOPqBhqX8&yt:cc=on" target="_blank">
<img src="https://img.youtube.com/vi/TxhOPqBhqX8/0.jpg" width="640" height="480" border="10" />
</a>
</div>
<br />


# Installation
<a name="installation"/>

To install an AlertR client or the AlertR server, please use the installation script. A detailed description of how to install an AlertR instance is given in the [Installation](https://github.com/sqall01/alertR/wiki/Installation) section of the wiki.


# Update
<a name="update"/>

If you have already a working AlertR system installed and a newer version is available, use the update script to update your AlertR instances. A detailed description of how to update an AlertR instance is given in the [Update](https://github.com/sqall01/alertR/wiki/Update) section of the wiki.


# Further Notes
<a name="further_notes"/>

If you are interested in AlertR and its development, you can also read AlertR related articles in my [Blog](http://h4des.org/blog/index.php?/categories/22-alertR). To post your awesome projects or ask a community for help you can use [reddit](https://www.reddit.com/r/AlertR/).


# Supporting AlertR
<a name="supporting_alertr"/>

If you like this project you can help to support it by contributing to it. You can contribute by writing tutorials, creating and documenting exciting new ideas to use AlertR (for example on [reddit](https://www.reddit.com/r/AlertR/)), writing code for it, and so on.

If you do not know how to do any of it or do not have the time, you can support the project by [donating](https://alertr.de/donations.php) or support me on [Patreon](https://www.patreon.com/sqall). Since services such as the push notification service have a monthly upkeep, the donation helps to keep these services free for everyone.

[![Patreon](https://c5.patreon.com/external/logo/become_a_patron_button.png)](https://www.patreon.com/sqall)

[![Donate](https://www.paypalobjects.com/en_US/DE/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=TVHGG76JVCSGC)


# Bugs and Feedback
<a name="bugs_and_feedback"/>

For questions, bugs and discussion please use the [Github Issues](https://github.com/sqall01/alertR/issues).