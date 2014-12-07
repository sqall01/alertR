package org.h4des.alertrmobilemanager;

import android.os.Bundle;
import android.preference.PreferenceActivity;

/*

written by sqall
twitter: https://twitter.com/sqall01
blog: http://blog.h4des.org
github: https://github.com/sqall01

Licensed under the GNU Public License, version 2.

*/

public class SettingsActivity extends PreferenceActivity  {
	@Override
	public void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		addPreferencesFromResource(R.xml.preferences);
	}
}
