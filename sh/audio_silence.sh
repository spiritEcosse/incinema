#!/bin/bash

# audio-silence add silent audio to a video clip

# e - script stops on error (return != 0)
# u - error if undefined variable
# o pipefail - script fails if one of piped command fails
# x - output each line (debug)
set -euox pipefail

# script usage
usage ()
{
# if argument passed to function echo it
[ -z "${1}" ] || echo "! ${1}"
# display help
echo "\
# audio-silence add silent audio to a video clip

$(basename "$0") -i infile.(mp4|mkv|mov|m4v) -c (mono|stereo) -r (44100|48000) -o outfile.mp4
-i infile.(mp4|mkv|mov|m4v)
-c (mono|stereo) :optional agument # if option not provided defaults to mono
-r (44100|48000) :optional agument # if option not provided defaults to 44100
-o outfile.mp4   :optional agument # if option not provided defaults to infile-name-silence-date-time"
exit 2
}

# error messages
NOTFILE_ERR='not a file'
INVALID_OPT_ERR='Invalid option:'
REQ_ARG_ERR='requires an argument'
WRONG_ARGS_ERR='wrong number of arguments passed to script'
NOT_MEDIA_FILE_ERR='is not a media file'

# if script is run arguments pass and check the options with getopts,
# else display script usage and exit
[ $# -gt 0 ] || usage "${WRONG_ARGS_ERR}"

# getopts check and validate options
while getopts ':i:c:r:o:h' opt
do
  case ${opt} in
     i) infile="${OPTARG}"
	[ -f "${infile}" ] || usage "${infile} ${NOTFILE_ERR}";;
     c) channel="${OPTARG}"
        { [ "${channel}" = 'mono' ] || [ "${channel}" = 'stereo' ]; } || usage;;
     r) rate="${OPTARG}"
        { [ "${rate}" = '44100' ] || [ "${rate}" = '48000' ]; } || usage;;
     o) outfile="${OPTARG}";;
     h) usage;;
     \?) usage "${INVALID_OPT_ERR} ${OPTARG}" 1>&2;;
     :) usage "${INVALID_OPT_ERR} ${OPTARG} ${REQ_ARG_ERR}" 1>&2;;
  esac
done
shift $((OPTIND-1))

# infile, infile
infile_nopath="${infile##*/}"
infile_name="${infile_nopath%.*}"

# file command check input file mime type
filetype="$(file --mime-type -b "${infile}")"

# video mimetypes
mov_mime='video/quicktime'
mkv_mime='video/x-matroska'
mp4_mime='video/mp4'
m4v_mime='video/x-m4v'

# check the files mime type is a video
#case "${filetype}" in
#    ${mov_mime}|${mkv_mime}|${mp4_mime}|${m4v_mime});;
#    *) usage "${infile} ${NOT_MEDIA_FILE_ERR}";;
#esac

# defaults for variables if not defined
channel_default='mono'
rate_default='44100'
outfile_default="${infile_name}-silence-$(date +"%Y-%m-%d-%H-%M-%S").mp4"

# check if the libfdk_aac codec is installed, if not fall back to the aac codec
aac_codec="$(ffmpeg -hide_banner -stats -v panic -h encoder=libfdk_aac)"
aac_error="Codec 'libfdk_aac' is not recognized by FFmpeg."
aac_check="$(echo "${aac_codec}" | grep "${aac_error}")"

# check ffmpeg aac codecs
if [ -z "${aac_check}" ]; then
   aac='libfdk_aac' # libfdk_aac codec is installed
else
   aac='aac' # libfdk_aac codec isnt installed, fall back to aac codec
fi

# video function
video_silence () {
  ffmpeg \
  -hide_banner \
  -stats -v panic \
  -f lavfi \
  -i anullsrc=channel_layout="${channel:=${channel_default}}":sample_rate="${rate:=${rate_default}}" \
  -i "${infile}" \
  -shortest -c:v copy -c:a "${aac}" \
  -movflags +faststart -f mp4 \
  "${outfile:=${outfile_default}}"
}

# video and audio function
video_audio_silence () {
  ffmpeg \
  -hide_banner \
  -stats -v panic \
  -f lavfi \
  -i anullsrc=channel_layout="${channel:=${channel_default}}":sample_rate="${rate:=${rate_default}}" \
  -i "${infile}" \
  -shortest -c:v copy -c:a "${aac}" \
  -map 0:v -map 1:a \
  -movflags +faststart -f mp4 \
  "${outfile:=${outfile_default}}"
}

# check if the video has an audio track
audio_check="$(ffprobe -i "${infile}" -show_streams -select_streams a -loglevel error)"

# check if audio_check is null which means the video doesnt have an audio track
if [ -z "${audio_check}" ]; then
   video_silence "${infile}" # null value
else
   video_audio_silence "${infile}" # non null value
fi
