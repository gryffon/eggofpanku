#
# I apologize for the mess this thing is; it's not really meant to work well
# on any system other than my own (right now, anyway). It's really only useful
# if you plan on distributing your own Egg of P'an Ku binaries.
#
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

import guids


NSIS_DIR = 'g:\\development\\tools\\nsis'
UPX_DIR = 'g:\\development\\tools\\upx'

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
            name="Microsoft.Windows.Common-Controls"
            version="6.0.0.0"
            processorArchitecture="X86"
            publicKeyToken="6595b64144ccf1df"
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
OutFile "eopk-%%%VERSION%%%-win32.exe"

InstallDir "$PROGRAMFILES\%%%APPNAME%%%"
InstallDirRegKey HKCU "Software\%%%APPNAME%%%" ""

LangString Homepage ${LANG_ENGLISH} "Visit eopk.monkeyblah.com for more information."
LangString HomepageLink ${LANG_ENGLISH} "http://eopk.monkeyblah.com/"

;--------------------------------------------------------
XPStyle on
SetCompressor lzma

;--------------------------------------------------------
!define MUI_ABORTWARNING
!define MUI_WELCOMEFINISHPAGE_BITMAP "..\\installer_image.bmp"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "license.txt"

!insertmacro MUI_PAGE_DIRECTORY

!define MUI_STARTMENUPAGE_REGISTRY_ROOT HKCU
!define MUI_STARTMENUPAGE_REGISTRY_KEY "Software\\%%%APPNAME%%%" 
!define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "Start Menu Folder"
Var StartMenuFolder
!insertmacro MUI_PAGE_STARTMENU Application $StartMenuFolder

!insertmacro MUI_PAGE_INSTFILES

!define MUI_FINISHPAGE_RUN "$INSTDIR\\EoPK.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Run %%%APPNAME%%% now"
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
  
!insertmacro MUI_LANGUAGE "English"

;--------------------------------------------------------
Section ""
  SetOutPath "$INSTDIR"
  
  %%%FILES%%%
  
  SetOutPath "$INSTDIR"
  
  WriteRegStr HKCU "Software\\%%%APPNAME%%%" "" $INSTDIR
  WriteUninstaller "$INSTDIR\\Uninstall.exe"
  
  !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
    CreateDirectory "$SMPROGRAMS\\$StartMenuFolder"
    CreateShortcut "$SMPROGRAMS\\$StartMenuFolder\\%%%APPNAME%%%.lnk" "$INSTDIR\\EoPK.exe"
    CreateShortcut "$SMPROGRAMS\\$StartMenuFolder\\Deck Editor.lnk" "$INSTDIR\\deckedit.exe"
    CreateShortcut "$SMPROGRAMS\\$StartMenuFolder\\Uninstall.lnk" "$INSTDIR\\Uninstall.exe"
    CreateShortcut "$SMPROGRAMS\\$StartMenuFolder\\Readme.txt.lnk" "$INSTDIR\\readme.txt"
  !insertmacro MUI_STARTMENU_WRITE_END
SectionEnd

;--------------------------------------------------------
;Uninstaller Section
Section "Uninstall"

  %%%DELETEFILES%%%
  
  Delete "$INSTDIR\\cards.db"
  Delete "$INSTDIR\\eopk-settings"
  Delete "$INSTDIR\\EoPK.exe.log"
  Delete "$INSTDIR\\Uninstall.exe"
  RMDir "$INSTDIR\\images\\cards"
  RMDir "$INSTDIR\\images\\tokens"
  RMDir "$INSTDIR\\images\\markers"
  RMDir "$INSTDIR\\images"
  RMDir "$INSTDIR\\decks"
  RMDir "$INSTDIR\\sys"
  RMDir "$INSTDIR"

  !insertmacro MUI_STARTMENU_GETFOLDER Application $StartMenuFolder
  Delete "$SMPROGRAMS\\$StartMenuFolder\\%%%APPNAME%%%.lnk"
  Delete "$SMPROGRAMS\\$StartMenuFolder\\Deck Editor.lnk"
  Delete "$SMPROGRAMS\\$StartMenuFolder\\Uninstall.lnk"
  Delete "$SMPROGRAMS\\$StartMenuFolder\\Readme.txt.lnk"
  RMDir "$SMPROGRAMS\\$StartMenuFolder"

  DeleteRegKey /ifempty HKCU "Software\%%%APPNAME%%%"
SectionEnd
'''

if len(sys.argv) == 1:
	sys.argv.append("py2exe")
	sys.argv.append("-q")


deckfiles = ['decks\\Crab Followers.l5d', 'decks\\Dragon Ring Honor.l5d', \
			'decks\\Spider Enlightenment.l5d', 'decks\\Scorpion Ninja.l5d']
imagefiles = glob.glob('images\\*.jpg') + glob.glob('images\\*.png')
cardimagefiles = glob.glob('images\\cards\\*.jpg')
tokenimagefiles = glob.glob('images\\tokens\\*.png')
markerimagefiles = glob.glob('images\\markers\\*.png')

setup(
	windows=[{
			'script': 'EoPK.py',
			'icon_resources': [(0, 'icon.ico')],
			'other_resources': [(24, 1, manifestxml % guids.EOPK_APPNAME)],
			'name': guids.EOPK_APPNAME,
			'description': '%s - An unofficial online tabletop for Legend of the Five Rings' % guids.EOPK_APPNAME,
			'version': guids.EOPK_VERSION_FULL,
			'copyright': guids.EOPK_COPYRIGHT,
		},
		{
			'script': 'deckedit.py',
			'icon_resources': [(0, 'iconedit.ico')],
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
			'excludes':['doctest', '_ssl', 'optparse', 'Numeric', 'simplejson._speedups'],
			'optimize':2,
		},
	},
	data_files=[
		('.', ['readme.txt', 'license.txt', 'tokens.dat','markers.dat', 'sets.dat']),
		('decks', deckfiles),
		('images', imagefiles),
		('images\\cards', cardimagefiles),
		('images\\tokens', tokenimagefiles),
		('images\\markers', markerimagefiles),
	]
)

nsisfiles = [
	('.', ['EoPK.exe', 'deckedit.exe', 'MSVCR71.dll', 'msvcp71.dll', 'gdiplus.dll', 'python25.dll',
		'tokens.dat', 'markers.dat', 'sets.dat', 'readme.txt', 'license.txt']),
	('decks', deckfiles),
	('images', imagefiles),
	('images\\cards', cardimagefiles),
	('images\\tokens', tokenimagefiles),
	('images\\markers', markerimagefiles),
	('sys', ['sys\\%s' % f for f in os.listdir('dist\\sys')]),
]

# Copy additional DLLs
for f in ('msvcp71.dll', 'gdiplus.dll'):
	shutil.copy(f, 'dist')

# UPX executables
subprocess.Popen('%s\\upx.exe dist/*.exe dist/*.dll dist/sys/*.dll dist/sys/*.pyd' % (UPX_DIR), stdout=sys.stdout, stderr=sys.stderr, stdin=sys.stdin).wait()

# Write NSIS installer script and compile
nsis = nsis_template \
	.replace('%%%APPNAME%%%', guids.EOPK_APPNAME) \
	.replace('%%%VERSION%%%', guids.EOPK_VERSION_FULL) \
	.replace('%%%FILES%%%', '\n  '.join(('SetOutPath "$INSTDIR\\%s"\n  ' % dir) + ''.join('File "%s"\n  ' % file for file in files) for dir, files in nsisfiles)) \
	.replace('%%%DELETEFILES%%%', '\n  '.join(''.join(('Delete "$INSTDIR\\%s"\n  ' % file) for file in files) for dir, files in nsisfiles))
file('dist/eopk.nsi', 'wb').write(nsis)

try:
	os.makedirs(srcdest)
except:
	pass

subprocess.Popen('%s\\makensis dist\\eopk.nsi' % NSIS_DIR, stdout=sys.stdout, stderr=sys.stderr, stdin=sys.stdin).wait()

# Ensure target directory exists
srcdest = 'dist-src/eopk-%s-src' % guids.EOPK_VERSION_FULL
try:
	os.makedirs(srcdest)
except:
	pass

# Copy files
srcfiles = [
	('.', glob.glob('*.py') + ['readme.txt', 'license.txt']),
	('decks', deckfiles),
	('images', imagefiles),
	('images/cards', cardimagefiles),
	('images/tokens', tokenimagefiles),
	('images/markers', markerimagefiles),
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
