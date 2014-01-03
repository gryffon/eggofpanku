from distutils.core import setup
import py2exe
import sys
import os
import os.path
import fnmatch
import glob
import subprocess
import sys
import tarfile
import shutil

#Local Imports
from gui import guids

userdir = os.path.join(os.path.expanduser('~'), 'eopk')

#These may require updating depending on installed location of tools
NSIS_DIR = 'c:\\Program Files (x86)\\NSIS'
UPX_DIR = 'c:\\Program Files (x86)\\upx391w'

manifestxml = '''
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
<assemblyIdentity
	version="0.64.1.0"
	processorArchitecture="x86"
	name="Python"
	type="win32"
/>
<description>%s</description>
<dependency>
	<dependentAssembly>
		<assemblyIdentity
			type="win32"
			name="Microsoft.VC90.CRT"
			version="9.0.21022.8"
			processorArchitecture="X86"
			publicKeyToken="1fc8b3b9a1e18e3b"
			language="*"
		/>
	</dependentAssembly>
</dependency>
</assembly>
'''

nsis_template = '''
!include "MUI.nsh"
;--------------------------------------------------------
Name "%%%APPNAME%%%"
OutFile "eopk-install.exe"

InstallDir "$PROGRAMFILES\%%%APPNAME%%%"
InstallDirRegKey HKCU "Software\%%%APPNAME%%%" ""

LangString Homepage ${LANG_ENGLISH} "Visit http://www.evil-incorporated.net/eopk for more information."
LangString HomepageLink ${LANG_ENGLISH} "http://www.evil-incorporated.net/eopk"

;--------------------------------------------------------
XPStyle on
SetCompressor lzma

;--------------------------------------------------------
!define MUI_ABORTWARNING
!define MUI_ICON "..\\..\\images\\icon.ico"
!define MUI_WELCOMEFINISHPAGE_BITMAP "..\\..\\install\\installer_image.bmp"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE"

!insertmacro MUI_PAGE_DIRECTORY

!define MUI_STARTMENUPAGE_REGISTRY_ROOT HKCU
!define MUI_STARTMENUPAGE_REGISTRY_KEY "Software\\%%%APPNAME%%%"
!define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "Start Menu Folder"
Var StartMenuFolder
!insertmacro MUI_PAGE_STARTMENU Application $StartMenuFolder

!insertmacro MUI_PAGE_INSTFILES

!define MUI_FINISHPAGE_RUN "$INSTDIR\\eopk.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Run %%%APPNAME%%% now"
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

;--------------------------------------------------------
Section ""
  SetOutPath "$INSTDIR"

  Delete "$INSTDIR\\settings.xml"
  Delete "$INSTDIR\\cards.db"

  %%%FILES%%%

  %%%DATAFILES%%%

  SetOutPath "$INSTDIR"

  WriteRegStr HKCU "Software\\%%%APPNAME%%%" "" $INSTDIR
  WriteUninstaller "$INSTDIR\\Uninstall.exe"

  !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
    CreateDirectory "$SMPROGRAMS\\$StartMenuFolder"
    CreateShortcut "$SMPROGRAMS\\$StartMenuFolder\\%%%APPNAME%%%.lnk" "$INSTDIR\\EoPK.exe"
    CreateShortcut "$SMPROGRAMS\\$StartMenuFolder\\Deck Editor.lnk" "$INSTDIR\\deckedit.exe"
    CreateShortcut "$SMPROGRAMS\\$StartMenuFolder\\Uninstall.lnk" "$INSTDIR\\Uninstall.exe"
  !insertmacro MUI_STARTMENU_WRITE_END
SectionEnd

;--------------------------------------------------------
;Uninstaller Section
Section "Uninstall"

  %%%DELETEFILES%%%

  Delete "$INSTDIR\\cards.db"
  Delete "$INSTDIR\\eopk-settings"
  Delete "$INSTDIR\\settings.xml"
  Delete "$INSTDIR\\EoPK.exe.log"
  Delete "$INSTDIR\\eopk.log"
  Delete "$INSTDIR\\Uninstall.exe"
  Delete "$INSTDIR\\*.exe"
  Delete "$INSTDIR\\*.dll"
  Delete "$INSTDIR\\logs\*.*"
  RMDir "$PROFILE\\epok\\images\\cards"
  RMDir "$PROFILE\\epok\\images\\tokens"
  RMDir "$PROFILE\\epok\\images\\markers"
  RMDir "$PROFILE\\epok\\images"
  RMDir "$PROFILE\\epok\\decks"
  RMDir "$INSTDIR\\sys"
  RMDir "$INSTDIR\\logs"
  RMDir "$PROFILE\\epok"
  RMDir "$INSTDIR"

  !insertmacro MUI_STARTMENU_GETFOLDER Application $StartMenuFolder
  Delete "$SMPROGRAMS\\$StartMenuFolder\\%%%APPNAME%%%.lnk"
  Delete "$SMPROGRAMS\\$StartMenuFolder\\Deck Editor.lnk"
  Delete "$SMPROGRAMS\\$StartMenuFolder\\Uninstall.lnk"
  RMDir "$SMPROGRAMS\\$StartMenuFolder"

  DeleteRegKey /ifempty HKCU "Software\%%%APPNAME%%%"
SectionEnd
'''

#BEGIN CODE

#Create Windows Executables
if len(sys.argv) == 1:
	sys.argv.append("py2exe")
	sys.argv.append("-q")

#Make sure dlls are in path
sys.path.append("..\\dlls")

deckfiles = ['..\\decks\\Crab Followers.l5d', '..\\decks\\Dragon Kensai.l5d', \
			'..\\decks\\Spider Breeder.l5d', '..\\decks\\Scorpion Ninja.l5d', \
			 '..\\decks\\Pheonix Military.l5d', '..\\decks\\Unicorn Battle Maidens.l5d',
			 '..\\decks\\Crane Dueling.l5d' ]

imagefiles = glob.glob('..\\images\\*.jpg') + glob.glob('..\\images\\*.png')
cardimagefiles = glob.glob('..\\images\\cards\\*.jpg')
tokenimagefiles = glob.glob('..\\images\\tokens\\*.png')
markerimagefiles = glob.glob('..\\images\\markers\\*.png')

setup(
	windows=[{
			'script': 'program.py',
			'dest_base': 'EoPK',
			'icon_resources': [(0, '..\\images\\icon.ico')],
			'other_resources': [(24, 1, manifestxml % guids.EOPK_APPNAME)],
			'name': guids.EOPK_APPNAME,
			'description': '%s - An unofficial online tabletop for Legend of the Five Rings' % guids.EOPK_APPNAME,
			'version': guids.EOPK_VERSION_FULL,
			'copyright': guids.EOPK_COPYRIGHT,
		},
		{
			'script': 'gui\\deckedit.py',
			'icon_resources': [(0, '..\\images\\iconedit.ico')],
			'other_resources': [(24, 1, manifestxml % (guids.EOPK_APPNAME + ' Deck Editor'))],
			'name': guids.EOPK_APPNAME + ' Deck Editor',
			'description': 'Standalone deck editor for %s' % guids.EOPK_APPNAME,
			'version': guids.EOPK_VERSION_FULL,
			'copyright': guids.EOPK_COPYRIGHT,
		},
	],
	zipfile='sys/library.zip',
	options={
		'py2exe':{
			'excludes':['doctest', '_ssl', 'optparse', 'Numeric', 'simplejson._speedups', "Tkinter","tcl" ],
			'packages':['OpenGL'],
			'optimize':2,
		},
	},
	data_files=[
		('.', ['..\\README', '..\\LICENSE', '..\\CHANGES', '..\\filters.xml','..\\updates.xml']),
		('.',['..\\dlls\\DataHandler.dll','..\\dlls\\Ionic.Zip.dll','..\\dlls\\UpdaterClasses.dll']),
		('.',['..\\dlls\\msvcp90.dll','..\\dlls\\msvcr90.dll', '..\\dlls\\gdiplus.dll']),
		('dat', ['..\\dat\\tokens.dat','..\\dat\\markers.dat']),
		('decks', deckfiles),
		('images', imagefiles),
		('images\\cards', cardimagefiles),
		('images\\tokens', tokenimagefiles),
		('images\\markers', markerimagefiles),
	]
)

nsisfiles = [
	('.', ['EoPK.exe', 'deckedit.exe', 'MSVCR90.dll', 'python27.dll', 'README', 'LICENSE', 'CHANGES', 'updates.xml']), 
	('.',['msvcp90.dll', 'gdiplus.dll', 'DataHandler.dll', 'UpdaterClasses.dll','Ionic.Zip.dll',]),
	('sys', ['sys\\%s' % f for f in os.listdir('dist\\sys')]),
]

#Remove leading ..\\ from files arrays
nsisdeckfiles = [s.replace('..\\','') for s in deckfiles]
nsisimagefiles = [s.replace('..\\','') for s in imagefiles]
nsiscardimagefiles = [s.replace('..\\','') for s in cardimagefiles]
nsistokenimagefiles = [s.replace('..\\','') for s in tokenimagefiles]
nsismarkerimagefiles = [s.replace('..\\','') for s in markerimagefiles]

nsisdatafiles = [
	('.', ['filters.xml',]),
	('dat', ['dat\\tokens.dat','dat\\markers.dat']),
	('decks', nsisdeckfiles),
	('images', nsisimagefiles),
	('images\\cards', nsiscardimagefiles),
	('images\\tokens', nsistokenimagefiles),
	('images\\markers', nsismarkerimagefiles),
]

#Create Windows Installer

# UPX executables
subprocess.Popen('%s\\upx.exe dist/*.exe dist/*.dll dist/sys/*.dll dist/sys/*.pyd' % (UPX_DIR), stdout=sys.stdout, stderr=sys.stderr, stdin=sys.stdin).wait()

# Write NSIS installer script and compile
nsis = nsis_template \
	.replace('%%%APPNAME%%%', guids.EOPK_APPNAME) \
	.replace('%%%VERSION%%%', guids.EOPK_VERSION_FULL) \
	.replace('%%%FILES%%%', '\n  '.join(('SetOutPath "$INSTDIR\\%s"\n  ' % dir) + ''.join('File "%s"\n  ' % file for file in files) for dir, files in nsisfiles)) \
	.replace('%%%DATAFILES%%%', '\n  '.join(('SetOutPath "$PROFILE\\eopk\\%s"\n  ' % dir) + ''.join('File "%s"\n  ' % file for file in files) for dir, files in nsisdatafiles)) \
	.replace('%%%USERDIR%%%', userdir) \
	.replace('%%%DELETEFILES%%%', '\n  '.join(''.join(('Delete "$INSTDIR\\%s"\n  ' % file) for file in files) for dir, files in nsisfiles))
file('dist/eopk.nsi', 'wb').write(nsis)

try:
	sys.stdout.write('\r\n---------------------------------------------------------------\r\n making Dirs \r\n')
	os.makedirs(srcdest)
except:
	pass

subprocess.Popen('%s\\makensis dist\\eopk.nsi' % NSIS_DIR, stdout=sys.stdout, stderr=sys.stderr, stdin=sys.stdin).wait()

#Create Source Package

"""
Exclude Source Package for Now

# Ensure target directory exists
srcdest = 'dist-src/eopk-%s-src' % guids.EOPK_VERSION_FULL
try:
	os.makedirs(srcdest)
except:
	pass

# Copy files
srcfiles = [
	('.', glob.glob('*.py') + ['README', 'LICENSE', 'CHANGES']),
	('.', ['..\\README', '..\\LICENSE', '..\\CHANGES', '..\\filters.xml','..\\updates.xml']),
	('.',['..\\dlls\\DataHandler.dll','..\\dlls\\Ionic.Zip.dll','..\\dlls\\UpdaterClasses.dll']),
	('.',['..\\dlls\\msvcp90.dll','..\\dlls\\msvcr90.dll', '..\\dlls\\gdiplus.dll']),
	('dat', ['..\\dat\\tokens.dat','..\\dat\\markers.dat']),
	('decks', deckfiles),
	('images', imagefiles),
	('images\\cards', cardimagefiles),
	('images\\tokens', tokenimagefiles),
	('images\\markers', markerimagefiles),

	]
for dest, files in srcfiles:
	try:
		os.makedirs('%s/%s' % (srcdest, dest))
	except:
		pass
	for f in files:
		print f
		shutil.copy(f, '%s/%s' % (srcdest, dest))

# Tar.gz it up
tar = tarfile.open('%s.tar.gz' % srcdest, 'w:gz')
tar.add(srcdest, 'eopk-%s-src' % guids.EOPK_VERSION_FULL)
tar.close()
"""