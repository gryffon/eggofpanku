

                    EGG OF P'AN KU 0.9.3 (2010-January-26)

          an unofficial Legend of the Five Rings online tabletop


Table of Contents

  - Overview
  - License
  - Quickstart
  - Playing the Game
  - Communicating
  - Card Database
  - Using Image Packs
  - Technical Details
  - News & Changes



Overview

  Egg of P'an Ku is a program for playing the Legend of the Five Rings 
  collectible card game online. It acts as a virtual tabletop to which 
  people can connect and play the game using digital representations of cards.

  Egg of P'an Ku does not enforce any game rules, but merely takes care 
  of the tabletop itself, cards in and out of play, tokens, and players. 
  Other programs that function similarly are The Game or Gempukku for Legend of the Five Rings, 
  and Apprentice for Magic: the Gathering.

  This product is not in any way endorsed by or otherwise associated with 
  the Alderac Entertainment Group or any of their affiliates.

License

  Egg of P'an Ku is copyright (C) 2008 Peter C O Johansson.
  Paige Watson has been updating the source code from release version 0.8.0 onward. 
  This updated source code is available in a GZ zipped file or via an SVN server 
  from http://code.google.com/p/eopk

  It is Free Software, licensed under the GNU General Public License (version 2). 
  You are free to use, copy and modify this program subject to certain restrictions.
  For more information, see license.txt.

  If you are interested in working on the EoPK project, please contact Paige Watson at paigespam@gmail.com


Installation

Developers ONLY - Please see /docs/Developer Installation Guide.txt for instructions
on how to install the source and deveopment resources.

Download the installation executable file

  You can get it either from the Egg of P'an Ku Google Code site (http://code.google.com/p/eopk)
  or from the downloads page on http://www.l5rnw.com. 

  The Egg of P'an Ku application is will only run on MS Windows (XP, 2003 or Vista).
  There is no current Mac version. (If you are interested in porting the 
  Python code to Mac, let me know)

You need to install a card database (cards.xml)

  If you already have The Game or Gempukku installed, you can use that
  database, if not you can download the latest version from the downloads 
  page at http://www.l5rnw.com or from Kamisasori (http://www.Kamisasori.net)
  
  There are currently two versions, a "Samurai only" version and a "complete" 
  version. "Samurai only" is the reccomended version unless you are playing
  with legacy cards.

  Unzip the cards.zip into a folder that you can find later.

  **To update your local database (when new cards are released, say), simply 
  replace cards.xml and delete cards.db from the installation directory. The
  next time you run Egg of P'an Ku, the database will be reloaded.
  

Run the installer

  After the installer runs, it will ask you to start the application.
  When you first start the application, it will ask you to point to the 
  cards.xml file.


(optional)Download the image packs

  You will probably also want to download the image packs, at least for
  the edition that you are playing, You can find these on the
  Kamisasori (http://www.Kamisasori.net) web site.
  These image packs should be unzipped into the images/cards directory 
  after installing the application.

  For more on the image packs, see "Using Image Packs" below.


--------------------------------------------------------------------------------
 

Setting up the application

Settings and Properties

  One you've installed the application and started it up, you'll want 
  to look at the Settings dialog to configure the application to suit 
  your play style. You can find this by going to the File\Preferences menu item.

  There are three tabs that will let you customize your game table and play style.

  General

  This tab allows you to change the Player Name. The player name is the name 
  that will appear in the chat box and in the player list, when playing against 
  another person.

  Database/Images

  Database Settings will tell you when the database was made, where it came 
  from and the file path on your computer.
  You can choose to "Reload" it, if you have downloaded a newer version, or 
  You can choose to change the file you're using by choosing the "Change Database" button.
  Image Pack is where the application looks for the card images.
  
  Change the directory path by editing the text box.  The path should be 
  relative to the application.

  Playfield

  Canvas (or table top) background can be changed by choosing the background
  setting along with the color.
  You can also choose a background image by checking the box and choosing the file.

  Attachments allows you to select which cards can have other cards attached.
  By default, only Personalities can have attached card, but for ease of use,
  you may want to allow holdings and/or strongholds to have other cards attached. 

  **Don't confuse the ability to attach cards as a rules change. 
  I attach holdings to other holdings and events to strongholds to save space on
  the table top.

 Once you are done with setting up the application, you're ready to begin playing.


Hosting a table

  To play a game, you must first start a table server.

  Go to the File menu and click "Host Table".

  You will automatically connect to your own table (and so can others if
  you give them your hostname).

  If you wish to connect to another player hosted game, go to the File 
  Menu and click "Connect".

  Notice that when you start the host server, the chat area shows your IP
  address. This is the address that you want to give to any opponent that
  is trying to connect to your host.  Note that the port is included at
  the end of the IP address.  You must be on the same port, which by default
  is set to 18072.

  No game has been started yet, and there are no players; only connected clients.
  **This is like your local playgroup sitting around the table, but no one
  has gotten their decks out of their bags yet.


--------------------------------------------------------------------------------

 

Starting a game
  To start a game, clients must first join the game. Go to the File menu
  again, and select "Join Game". 
  
  You will be prompted to select a deck to play (a few are shipped with 
  Egg of P'an Ku, but of course you'll want to compose your own).

  If you want to test your deck by playing solo, you can just start the game.
  If not, once all clients interested in joining have done so, the host can
  start the game.

  Again in the File menu, select "Start Game".
  
  The server will set up the game, fetch each player's stronghold, and set
  starting honor as appropriate.


--------------------------------------------------------------------------------

 

Setting up the Playfield
  As mentioned above, your stronghold should be on the playfield, but not much else.

  Do these in any order:

  - Go to the Fate Deck menu and select "Draw Serveral" (<ctrl> + <shift> + D)
    or use the icon and draw 5 cards.

  - If you are going second, right click on your Dynasty Deck and choose
    "Look Through" (or select "Search" from the Dynasty Deck menu) and drag 
    a legacy holding onto the playfield. Double click it to bow it.

  - Drag 4 Dynasty cards from your Dynasty Deck pile to the playfield for
    your provinces.

Now your ready to start....

Enjoy!


Other helpful items:

Communicating

  Below the chat log is an entry box. You can use that to talk to your fellow
  players at the table.
  
  You can also use it to change your name; type '/name desiredname' to change
  your name. This change is persistent and saved to your settings, so you will
  not need to do it again next time you play.



Using Image Packs

  Egg of P'an Ku supports the same kind of image databases used by The Game
  and Gempukku v3 (although it also provides generic card images for any
  missing card images).
  
  To use image packs, simply extract them into the images/cards/ subdirectory
  in your installation directory, making sure to preserve their own directory
  names. In the end, the structure should look like this:
  
  Installation directory
  - EoPK.exe
  - readme.txt
  - images/
    - cards/
      - STS/
        - STS001.jpg
        - STS002.jpg
          ...
        HV/
        - HV001.jpg
        - HV002.jpg
          ...
        SE/
        - SE001.jpg
        - SE002.jpg
          ...

  And so forth, for any editions for which you have image packs. They will be
  automatically used by the program as appropriate.

  A good place to get image packs is Kamisasori no Kaisho, located at
    http://www.kamisasori.net/



Technical details

  Egg of P'an Ku is written in Python 2.5. It primarily uses wxPython 2.8 for
  user interface management, simplejson for network message serialization,
  pyOpenGL (through wx) for playfield rendering, PIL and wx for image loading,
  and various out-of-the-box Python modules for network management, card
  database storage, etc.
  
  If you are using a Win32 executable version of Egg of P'an Ku, it was
  packaged using py2exe.
  
  The default server port is 18072, so if you are behind a firewall and want
  to host games, that's the port you need to forward/open.



News & Changes

  2010-January-26 Egg of P'an Ku 0.9.3
	* Fixed issue with honor Req for Followers not showing up.
	* Fixed problem with the "Show card to Opponent" menu option not working preoperly.


  2009-August-24 Egg of P'an Ku 0.9.21
	* Fixed problem with strongholds not being added to new decks.

  2009-August-24 Egg of P'an Ku 0.9.21
	* Added "Celestial" card type
	* Fixed R55 to show correct Fate card count in the Deckeditor text window.
	* changed code to work with new version of the cards.xml with singular card types and "strategy" instead of "actions"

  2009-July-1 Egg of P'an Ku 0.9.10

	* CE Settings added to draw 6. (You can change back to 5 in preferences).
	* "Border Keep" and "Bamboo Harvesters" are automatically put into play.
		- This can be turned off in the preferences.
	* Fixed the Shuffling (back to before) and added a random counter to it.

  2009-Feb-12 Egg of P'an Ku 0.9.01

	* Double clicking a face down card will now turn it face up.  Double clicking face up
		cards will bow/straighten them.
	* Added a setting in the preferences to log multiplayer games to a file.
	* Moved a lot of the souce code to files that can be updated without reinstalling.
	* Changed Shuffling algorithm to shuffle better
	* Fixed problem with showing opponent a face down card (revealed to player also).
	* Fixed issue 26 (Deck Editor needs to be able to filter on "CE" edition cards.)
	* Fixed issue 28 (Add "Celestial Edition" to the filters list)
	* Fixed issue 30 (Legacy keyword) - should not appear in dialogs 
	* Fixed issue 33 (Remove 'Monkey' from minor clan list)
	* Fixed issue 35 (Manipulating discard and dead piles) - you can now rehonor a dead card.



  2008-Dec-11 Egg of P'an Ku 0.9.0

	* Fixed issue 15 (Cards not sorting for Toturi's Army)
	* Fixed issue 16 (Need converter for The Game and Gempukku decks) - You can now import these formats
	* Fixed issue 17 (Possible Quck flip option) - You can now center (wheel) click a card to flip it.
	* Added issue 19 (Add "put on bottom/top of deck" to right click menu)
	* Added issue 14 (Can't easily put cards on deck bottoms) - Same as 19, but from all card lists!
	* Added issue 21 (Add auto-draw functionality when the game starts) - now draws 5 cards for each player.
	* Added issue 22 (Place 4 Dynasty cards on the playfield at start) - now draws 4 cards for each player on thier play field.
	* Added issue 24 (Can't show face down card to opponent) - you can now right click to show a face down card to an opponent, without see it yourself
	* Added the enums.py to the EoPK source for others to use.
	* Added the odict.py to the EoPK source for others to use.
	* Added a Docs directory to the SVN Source
	* Updated the .tar zipped source code to contain all the files needed to build EoPK

  2008-Dec-05 Egg of P'an Ku 0.8.6

	* Fixed issue 11 (attach list in settings-ui too small) 
	* Fixed issue 13 (Change the card text font to a more readable font) to make the card text a little larger
	* updated the HTML output to a little better format
	* updated the readme.txt to include the newer instructions.

  2008-Nov-26 Egg of P'an Ku 0.8.5

	* moved the import menu item to the Edit menu.
	* Added the ability to copy the current deck to the clipboard as BBCode or HTML
	* Changed the look of the deck list to include card counts and seperate list into card types.

  2008-Nov-17 Egg of P'an Ku 0.8.4

	* Added the ability to import a decklist from the clipboard.
	* Added Winds to the deck editor (and by default then, to all decks)
	* Fixed a bug that wouldn't allow you to discard or destroy a card with markers on it.
	* Changed the order that the sets are listed in the deck editor dropdown to chronological.
	* Changed the Clan filter dropdown to list great clans first then minor/others.
	* Fixed a bug that wouldn't allow you to discard or destroy a card with markers on it.

  2008-Nov-6 Egg of P'an Ku 0.8.3

	* Added Custom Markers, including custom marker images, the default being generic.
	* Fixed a bug with removing all markers and marker display.

  2008-Oct-8 Egg of P'an Ku 0.8.2

	* Markers were added to the game. Like Tokens, you can put attach these to a
	card to show value changes. Unlike tokens, the markers are removed when a 
	player unbows all his cards (signalling the start of a turn), or they can be
	removed by the "remove markers" menu item and buttons
	* Added Marker images
	* Added a toolbar item to "remove all markers" from all cards in play on a players side.
	* Straighten all now removes all markers from a players side as well.
	

  2008-Jun-4 Egg of P'an Ku 0.8.0

    * They playfield is now split into compartments, one for each player.
    Playfields belonging to other players are rotated 180 degrees.
    * It is now possible to look at other players' discard piles.
    * Playfields can be zoomed with the scroll wheel.
    * A toolbar with common game actions has been added to the client.
    * The playfield background can be customized with colors and images.
    * A bug with changing control of cards was fixed.
    * Holding cards can now be created.
    * It is now possible to customize what card types are eligible for
      attaching cards to.
    * Hovering over cards in a playfield now displays a tooltip with some
      additional information.
    * The deck editor how has a "recent decks" section in the File menu.
    * The (first) local network address is now shown when a server is started.

  2008-May-24 Egg of P'an Ku 0.7.0
    
    * It is now possible to attach cards to other cards. Simply drag a card
      onto another card and they will snap onto each other and will move as
      a unit. It's only possible to do this with a card that doesn't already
      have attached cards (because that is just silly).
    * A preferences dialog has been added to the main client where a number
      of configuration options can be changed.
    * If a cards.xml file is defined, and the local database is older, it
      will now be automatically re-imported on program start.
    * The dynasty and fate decks were switched around in the main window,
      so that they are in the same order as in real life.
    * Rulings are now available along with card text for cards that have them.
      NOTE: If upgrading from an older version, the card database needs to be
      reloaded before this feature will work.
    * Format legality is now shown along with card text.
    * Alt-drag now works properly for focus pools.
    * Added the ability to sort card lists by card attributes in the
      deck editor by clicking their respective columns.
    * Cards are now sorted by name by default in the deck editor.
    * There is now an alternative plaintext view for easier copying of deck
      lists to other media, such as forums.
    * Removing 3 of one card when you had less than 3 already no longer
      results in having a negative number of cards.
    * A few files were renamed and a sets.dat file was added that contains a
      list of card sets.
    * Fixed a bug that prematurely closed deck inspection windows when another
      player shuffled his or her same deck.
    * Fixed a bug that might result in conflicting network protocol versions
      not being properly detected.
    * Miscellaneous typos were fixed.
    * Fixed inappropriate messages shown when moving cards out of decks.
    
  2008-May-10 Egg of P'an Ku 0.6.1
  
    * Fixed a bug where SO_REUSEADDR was not set properly.
    * Fixed a bug where the port entry when connecting was not respected.
  
  2008-May-7 Egg of P'an Ku 0.6.0
  
    * Filter interface changed slightly and a few new filters added.
    * Card name and text filters now accept regular expressions.
    * New chat widget with clickable card names added.
    * Added a sticky-move option (ctrl-drag or middle-mouse-drag) that moves
      all overlapping cards in a pile in play at once.
    * Added menu commands for revealing cards from your fate hand.
    * Changed "drag face down" to shift-drag rather than right-drag. This
      behavior is now standard throughout the client.
    * Made it possible to drag cards to the bottoms of zones by alt-dragging.
    * For dragging from decks, ctrl-drag now moves the bottom card in that
      pile rather than the top card.
    * When searching through decks, Legacy holdings are now specially marked.
    * Added protocol verification to the network handshake process.
    * Added better save confirmation dialogs for the deck editor.
    * Double-clicking cards in the deck editor now adds them to the deck.
    * Fixed (hopefully) a bug where chat lines could get cut off.
    * Fixed incorrect messages shown when moving fate cards into a player's
      hand when the card was coming from a deck.
    * Fixed errors arising from cards not being in the local database.
    * The exit menu option actually works now.
    
  2008-Apr-25 Egg of P'an Ku 0.5.0

    * Added the Imperial Favor to the game.
    * Made it possible to give control of cards in play to other players.
    * Made it possible to start a new game without restarting the client and
      added a confirmation dialog for this.
    * You can now leave the game after submitting a deck.
    * Made it so only one card can be selected at a time in the deck editor.
    * Added filters for gold cost to the deck editor.
    * A bug where focus pools would end up with cards from the opponent's pool
      in them was fixed.
    * A deck editor bug where window title wouldn't update properly was fixed.
    * A bug where it was possible to start a game with no players was fixed.

  2008-Apr-16 Egg of P'an Ku 0.4.0

    * A deck editor has been added.
    * A new focus pool zone has been created.
    * A full complement of generic card images has been added.
    * Card previews now show card type in addition to other information.
    * Context menu options were added for rearranging the Z-order of cards
      while in play.
    * Chatting now flashes the play window if not active.
    * Rearranging cards in your hand was disabled.
    * A bug where spells were not listed as fate cards was fixed.
    * A bug that made it possible to hide the playfield forever with the main
      splitter window was fixed.
    * Dragging bowed cards in play now shows the correct marker.
  
  2008-Apr-9 Egg of P'an Ku  0.3.0

    * First semi-official release.



Egg of P'an Ku is Copyright (C) 2008 Peter C O Johansson.

Modifications to this source were done by Paige Watson
Copryright (C) 2010 Paige C. Watson

Download new versions at http://www.eggofpanku.com
Source code is available at http://code.google.com/p/eopk



