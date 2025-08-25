#----------------------------------------------#
#------------- install yt-dlp -----------------#
#----------------------------------------------#

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

