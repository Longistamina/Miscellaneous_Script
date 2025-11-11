#----------------------------------------------#
#------------- install yt-dlp -----------------#
#----------------------------------------------#

# Remove old yt-dlp if needed
rm ~/.local/bin/yt-dlp

# Download the current nightly build
sudo curl -L https://github.com/yt-dlp/yt-dlp-nightly-builds/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp

# Make executable
sudo chmod a+rx /usr/local/bin/yt-dlp

# Restart your shell session to enable yt-dlp
exec bash

# Remove cache
yt-dlp --rm-cache-dir


#------------------------------------------------------#
#------------- download youtube video -----------------#
#------------------------------------------------------#

yt-dlp --merge-output-format mp4 -f "bestvideo+bestaudio" -o "/home/longdpt/Videos/%(title)s.%(ext)s" https://youtu.be/m3PguKYQXAY

# Download with output as .mp4
# with bestvideo and bestaudio quality
# output in /home/longdpt/Videos/
# Input url is: https://youtu.be/m3PguKYQXAY


#-----------------------------------------------------------------------------------------------#
#------------- download youtube with some restrictions (like Age verification) -----------------#
#-----------------------------------------------------------------------------------------------#

# Install secretstorage to help bypass cookies
python3 -m pip install secretstorage

# Download with --cookies-from-browser [browser name]
yt-dlp --cookies-from-browser brave --merge-output-format mp4 -f "bestvideo+bestaudio" -o "/home/longdpt/Videos/%(title)s.%(ext)s" https://www.youtube.com/watch?v=5zYBZi34bDo

# --cookies-from-browser brave (brave is the browser name, if you google chrome => chrome)
