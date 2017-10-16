package org.h4des.alertrmobilemanager;

import android.os.Bundle;
import android.preference.PreferenceManager;
import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.webkit.HttpAuthHandler;
import android.webkit.WebChromeClient;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.support.v4.app.NavUtils;

/*

written by sqall
twitter: https://twitter.com/sqall01
blog: http://blog.h4des.org
github: https://github.com/sqall01

Licensed under the GNU Affero General Public License, version 3.


used icon from author "AhaSoft" licensed under Creative Commons Attribution 3.0 Unported License
*/

public class MainActivity extends Activity {

	public WebView webView = null; 
	
    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        this.webView = (WebView)findViewById(R.id.webView);
                      
        // clear cache
        this.webView.clearCache(true);
       
        // enable JavaScript
        this.webView.getSettings().setJavaScriptEnabled(true);
        
        this.webView.setWebChromeClient(new WebChromeClient());                                                      
               
        // create own WebViewClient
        this.webView.setWebViewClient(new WebViewClient() {
 
            // for debugging in the emulator only
            // install your own certificate on the android device via copying your cert.cer
            // on the sd card and add it in the security options
            //@Override
            //public void onReceivedSslError (WebView view, SslErrorHandler handler, SslError error) {            
            //    handler.proceed();
            //}
        	
        	
            // when using basic http authentication
            // enter your own credentials
            @Override
            public void onReceivedHttpAuthRequest(WebView view, HttpAuthHandler handler, String host, String realm) {
            	
        		// get username and password from the settings
        		SharedPreferences preferences = PreferenceManager.getDefaultSharedPreferences(MainActivity.this);
        		String username = preferences.getString("username", "None");
        		String password = preferences.getString("password", "None");            	          	
            	
        		// use credentials from the settings
            	handler.proceed(username, password);
            }
        });                  
        
		// get URL from the settings
		SharedPreferences preferences = PreferenceManager.getDefaultSharedPreferences(MainActivity.this);        
        String url = preferences.getString("url", "None");
        
        this.webView.loadUrl(url);
                     
        // focus webView
        this.webView.requestFocus(View.FOCUS_DOWN);        
    }
    
	  @Override
	  public boolean onCreateOptionsMenu(Menu menu) {
	      super.onCreateOptionsMenu(menu);
	      // generating exit button in the menu
	      menu.add(Menu.NONE, 0, Menu.NONE, "Exit Application");
	      menu.add(Menu.NONE, 1, Menu.NONE, "Settings");
	      return true;
	  }    
	  
	  // execute when a menu option is pressed
	  public boolean onOptionsItemSelected(MenuItem item){
		  switch (item.getItemId()) {
				case 1:
					Intent intent = new Intent(MainActivity.this, SettingsActivity.class);
					startActivity(intent);
					break;		  
	      		case 0:
	      		default:
	      			// exit application
	      			finish();
	        	}
	      return false;
	  }	  
}
