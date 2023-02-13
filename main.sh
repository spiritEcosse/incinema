#!/bin/bash

# e - script stops on error (return != 0)
# u - error if undefined variable
# o pipefail - script fails if one of piped command fails
# x - output each line (debug)
set -euox pipefail

PATH_FONT=$(pwd)"/static/OpenSans/OpenSans-Regular.ttf"
FILE_CUT="cut_list.txt"
ORIGINAL_FILE="fall.mp4"
FILE_CUT_DURATION="cut_list_duration.txt"
SCENE_DETECT_RESTORE=0
SCENE_RANDOM_RESTORE=1
SCENE_CUT_RESTORE=1
CONCAT_VIDEOS=1
REDRAW_ON_VIDEO=1
READD_AUDIO=1
MY_TEXT="Fall / Вышка
Рік\:  2022
Країна\:  США
Режисери\:  Скотт Манн
Тривалість\:  107 хв
Рейтинг IMDB\:  6.40/10 (Голосів\: 52 551)
"
FONT_SIZE=24
FONT_COLOR=white
POSITION_X="20"
POSITION_Y="h-text_h-20"


audio_silence() {
#  ../sh/audio_silence.sh -i "${ORIGINAL_FILE}" -o "${SILENCE_VIDEO}"
  if [[ ! -f ${SILENCE_VIDEO} ]]; then
    ffmpeg -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=44100 -i "${ORIGINAL_FILE}" -c:v copy -c:a aac -shortest "${SILENCE_VIDEO}"
  fi
}

scene_detect() {
  if [[ ! -f ${FILE_CUT} || ${SCENE_DETECT_RESTORE} == "1" ]]; then
    ../scene_detect.sh -i "${1}" -o ${FILE_CUT}
  fi
}

get_random_scene() {
  if [[ ! -f ${FILE_CUT_DURATION} || ${SCENE_RANDOM_RESTORE} == "1" ]]; then
    python ../main.py ${FILE_CUT} ${FILE_CUT_DURATION}
  fi
}

scene_cut() {
  if [[ ${SCENE_CUT_RESTORE} == "1" ]]; then
    rm -f fall-*
    ../scene_cut.sh -i "${1}" -c ${FILE_CUT_DURATION}
  fi
}

concat_videos() {
  if [[ ! -f ${CONCATED_VIDEO} || ${CONCAT_VIDEOS} == "1" ]]; then
    ffmpeg -y -f concat -safe 0 -i <(for f in $(ls $(pwd)/*-[0-9]*.mp4 | sort -V); do echo "file '$f'"; done) -c copy "${CONCATED_VIDEO}"
  fi
}

draw_on_video() {
  if [[ ! -f ${CONCATED_DRAWED_VIDEO} || ${REDRAW_ON_VIDEO} == "1" ]]; then
    ffmpeg -y -i "${CONCATED_VIDEO}" -vf drawtext="fontfile=${PATH_FONT}: text='${MY_TEXT}': fontsize=${FONT_SIZE}: fontcolor=${FONT_COLOR}: x=${POSITION_X}: y=${POSITION_Y}" -codec:a copy "${CONCATED_DRAWED_VIDEO}"
  fi
}

add_audio() {
  if [[ ! -f ${ADDED_AUDIO_FILE} || ${READD_AUDIO} == "1" ]]; then
#    ffmpeg -y -i "${CONCATED_DRAWED_VIDEO}" -i fall.mp3 -c copy "${ADDED_AUDIO_FILE}"
    ffmpeg -y -i "${CONCATED_DRAWED_VIDEO}" -i fall.mp3 -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 "${ADDED_AUDIO_FILE}"
  fi
}

cd fall
CONCATED_VIDEO=$(basename $(pwd))_final.mp4
CONCATED_DRAWED_VIDEO=$(basename $(pwd))_final_drawed.mp4
SILENCE_VIDEO=$(basename $(pwd))_silence.mp4
ADDED_AUDIO_FILE=$(basename $(pwd))_audio.mp4
audio_silence
scene_detect "${SILENCE_VIDEO}"
get_random_scene
scene_cut "${SILENCE_VIDEO}"
concat_videos "${SILENCE_VIDEO}"
draw_on_video
add_audio
