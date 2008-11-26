


                    EGG OF P'AN KU 0.8.2 (2008-Nov-17)

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
  collectible card game online. It acts as a virtual tabletop to which people
  can connect and play the game using digital representations of cards.
  
  Egg of P'an Ku does not enforce any game rules, but merely takes care of
  the tabletop itself, cards in and out of play, tokens, and players. Other
  programs that function similarly are The Game or Gempukku for Legend of the
  Five Rings, and Apprentice for Magic: the Gathering.
  
  This product is not in any way endorsed by or otherwise associated with the
  Alderac Entertainment Group or any of their affiliates.



License

  Egg of P'an Ku is copyright (C) 2008 Peter C O Johansson. It is also
  Free Software, licensed under the GNU General Public License (version 2).
  You are free to use, copy and modify this program subject to certain
  restrictions.
  
  For more information, see license.txt.



Quickstart

  First of all, you need to install a card database; see the section with that
  title below. If you already have The Game or Gempukku installed, you can use
  that database.

  To play a game, you must first start a table server. It's simple; just go to
  the File menu and click Host Table. You will automatically connect to your
  own table (and so can others if you give them your hostname).
  
  At the moment, no game has started, and there are no players; only connected
  clients. Compare it if you will to your local playgroup sitting around the
  table, but no one has gotten their decks out of their bags yet.
  
  To start a game, clients must first join the game. Go to the File menu
  again, and select Join Game. You will be prompted to select a deck to play
  with (a few are shipped with Egg of P'an Ku, but of course you'll want to
  compose your own).
  
  Once all clients interested in joining have done so, the host can start the
  game. Again in the File menu, select Start Game. The server will set up the
  game, fetch each player's stronghold, and set starting honor as appropriate.
  
  Your cards are probably going to be blank at this point. You need to get an
  image pack or two if you want pictures on your cards; see the section on
  that below for more information.



Playing the Game

  Most of a typical game is concerned with moving cards around. Doing so in
  Egg of P'an Ku is simple. Almost all card movement is done through simple
  drag-and-drop operations.
  
  In the lower left corner of the program is your fate hand, and above it is
  five piles corresponding to your removed-from-game pile, fate discard pile,
  fate deck, dynasty deck, and dynasty discard pile respectively. Cards can be
  dragged from or into any of these zones. The piles can also be right-clicked
  for additional actions.
  
  In the middle of the window is the playfield. Cards can be dragged to or
  from that as well. Cards dragged into play from decks will be placed 
  face-down by default. Cards dragged into play from hands or discard piles
  will be face-up by default. Holding shift when you begin dragging from your
  fate hand will drag the card face down, overriding the default.
  
  By default, cards will be moved from the top of each pile to the top of
  wherever the card is dragged. To move the bottom card of a pile, hold down
  ctrl as you begin dragging. To place the card on the bottom of the target
  pile instead of the top, hold down alt as you begin dragging.
  
  Cards in play can be manipulated in special ways. Right-clicking one of your
  cards in play will give you a popup menu listing ways you can interact with
  that card, such as bowing it, turning it face up or down, dishonoring it,
  and so forth. As a shortcut, double-clicking a card will toggle its bowed
  status.
  
  Furthermore, holding ctrl while dragging cards in play will move the card
  along with any other cards that overlap it. This is useful for moving entire
  units at once. Dragging with the middle mouse button behaves the same way.
  
  Clicking a card in your hand or in a deck, or hovering over a card in play,
  will show that card's text in the top left pane of the main window. You can
  also click card names as they show up in the log at the bottom of the screen
  to preview them.
  
  Egg of P'an Ku keeps track of family honor and the Imperial Favor as well.
  Using the Game menu, you can manipulate these elements, as well as roll
  dice or flip coins, or put token cards into play.



Communicating

  Below the chat log is an entry box. You can use that to talk to your fellow
  players at the table.
  
  You can also use it to change your name; type '/name desiredname' to change
  your name. This change is persistent and saved to your settings, so you will
  not need to do it again next time you play.



Card Database

  Egg of P'an Ku requires a database of cards to function. The first time you
  run the program, or if the locally cached database is deleted, you will need
  to import a card database. It will then be stored in a format that's a bit
  easier for Egg of P'an Ku to load (a Python pickle).
  
  Databases are imported from the same XML format used by The Game and
  Gempukku v3, and by default Egg of P'an Ku will look for a file called
  cards.xml in its installation directory. If it doesn't exist, you will be
  prompted to import it from elsewhere. In either case, a local database will
  be created from it. You will not need the XML file after this, unless your
  local database is deleted.
  
  To update your local database (when new cards are released, say), simply 
  replace cards.xml and delete cards.db from the installation directory. The
  next time you run Egg of P'an Ku, the database will be reloaded.
  
  A good place to get card databases is Kamisasori no Kaisho, located at
    http://www.kamisasori.net/



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

Download new versions at http://code.google.com/p/eopk/
Origianl website is http://www.monkeyblah.com.


