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




NSIS_DIR = 'c:\\Program Files\\NSIS'
UPX_DIR = 'c:\\upx'

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
OutFile "eopk-install.exe"

InstallDir "$PROGRAMFILES\%%%APPNAME%%%"
InstallDirRegKey HKCU "Software\%%%APPNAME%%%" ""

LangString Homepage ${LANG_ENGLISH} "Visit http://www.eggofpanku.com for more information."
LangString HomepageLink ${LANG_ENGLISH} "http://www.eggofpanku.com"

;--------------------------------------------------------
XPStyle on
SetCompressor lzma

;--------------------------------------------------------
!define MUI_ABORTWARNING
!define MUI_ICON "..\\icon.ico"
!define MUI_WELCOMEFINISHPAGE_BITMAP "..\\installer_image.bmp"

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

  SetOutPath "$INSTDIR"

  WriteRegStr HKCU "Software\\%%%APPNAME%%%" "" $INSTDIR
  WriteUninstaller "$INSTDIR\\Uninstall.exe"

  !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
    CreateDirectory "$SMPROGRAMS\\$StartMenuFolder"
    CreateShortcut "$SMPROGRAMS\\$StartMenuFolder\\%%%APPNAME%%%.lnk" "$INSTDIR\\EoPK.exe"
    CreateShortcut "$SMPROGRAMS\\$StartMenuFolder\\Deck Editor.lnk" "$INSTDIR\\deckedit.exe"
    CreateShortcut "$SMPROGRAMS\\$StartMenuFolder\\Update (required only).lnk" "$INSTDIR\\eggupdater.exe"
    CreateShortcut "$SMPROGRAMS\\$StartMenuFolder\\Update (include optional updates).lnk" "$INSTDIR\\eggupdater.exe" "-optional"
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
  RMDir "$INSTDIR\\images\\cards"
  RMDir "$INSTDIR\\images\\tokens"
  RMDir "$INSTDIR\\images\\markers"
  RMDir "$INSTDIR\\images"
  RMDir "$INSTDIR\\decks"
  RMDir "$INSTDIR\\sys"
  RMDir "$INSTDIR\\logs"
  RMDir "$INSTDIR"

  !insertmacro MUI_STARTMENU_GETFOLDER Application $StartMenuFolder
  Delete "$SMPROGRAMS\\$StartMenuFolder\\%%%APPNAME%%%.lnk"
  Delete "$SMPROGRAMS\\$StartMenuFolder\\Deck Editor.lnk"
  Delete "$SMPROGRAMS\\$StartMenuFolder\\Update (Required only).lnk"
  Delete "$SMPROGRAMS\\$StartMenuFolder\\Update (include optional updates).lnk"
  Delete "$SMPROGRAMS\\$StartMenuFolder\\Uninstall.lnk"
  RMDir "$SMPROGRAMS\\$StartMenuFolder"

  DeleteRegKey /ifempty HKCU "Software\%%%APPNAME%%%"
SectionEnd
'''

##sys.stdout = open('py2exe-output.log','w')


if len(sys.argv) == 1:
	sys.argv.append("py2exe")
	sys.argv.append("-q")


deckfiles = ['decks\\Crab Followers.l5d', 'decks\\Dragon Kensai.l5d', \
			'decks\\Spider Breeder.l5d', 'decks\\Scorpion Ninja.l5d', \
			 'decks\\Pheonix Military.l5d', 'decks\\Unicorn Battle Maidens.l5d',
			 'decks\\Crane Dueling.l5d' ]

imagefiles = glob.glob('images\\*.jpg') + glob.glob('images\\*.png')
cardimagefiles = glob.glob('images\\cards\\*.jpg')
tokenimagefiles = glob.glob('images\\tokens\\*.png')
markerimagefiles = glob.glob('images\\markers\\*.png')

setup(
	windows=[{
			'script': 'program.py',
			'dest_base': 'EoPK',
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
			'excludes':['doctest', '_ssl', 'optparse', 'Numeric', 'simplejson._speedups',
						"Tkinter","tcl" ],
			'packages':['OpenGL'],
			'optimize':2,
		},
	},
	data_files=[
		('.', ['README', 'LICENSE', 'CHANGES', 'tokens.dat','markers.dat',  'filters.xml','updates.xml']),
		('dlls',['DataHandler.dll','Ionic.Zip.dll','UpdaterClasses.dll'])
		('scripts',['eggupdater.exe','copyninja.exe'])
		('decks', deckfiles),
		('images', imagefiles),
		('images\\cards', cardimagefiles),
		('images\\tokens', tokenimagefiles),
		('images\\markers', markerimagefiles),
	]
)

nsisfiles = [
	('.', ['EoPK.exe', 'deckedit.exe', 'MSVCR90.dll', 'python25.dll', 'tokens.dat', 'markers.dat', 
			 'README', 'LICENSE', 'CHANGES', 'filters.xml','updates.xml']), 
	('dlls',['msvcp90.dll', 'gdiplus.dll', 'DataHandler.dll', 'UpdaterClasses.dll','Ionic.Zip.dll',])
	('scripts',['eggupdater.exe','copyninja.exe'])
	('decks', deckfiles),
	('images', imagefiles),
	('images\\cards', cardimagefiles),
	('images\\tokens', tokenimagefiles),
	('images\\markers', markerimagefiles),
	('sys', ['sys\\%s' % f for f in os.listdir('dist\\sys')]),
]

# Copy additional DLLs
for f in ('dlls/msvcp90.dll', 'dlls/msvcr90.dll', 'dlls/gdiplus.dll', 'dlls/DataHandler.dll','eggupdater.exe','dlls/UpdaterClasses.dll','dlls/Ionic.Zip.dll','copyninja.exe'):
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
	sys.stdout.write('\r\n---------------------------------------------------------------\r\n making Dirs \r\n')
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
	('.', glob.glob('*.py') + glob.glob('*.ico') + ['README', 'LICENSE', 'CHANGES','tokens.dat','markers.dat','installer_image.bmp','gdiplus.dll','msvcr90.dll','msvcp90.dll','DataHandler.dll','eggupdater.exe','UpdaterClasses.dll','Ionic.Zip.dll','copyninja.exe']),
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
