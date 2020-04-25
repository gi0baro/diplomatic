ARG SRC_IMAGE

FROM ${SRC_IMAGE}

WORKDIR /app

COPY diplomacy diplomacy
COPY nudiplomacy nudiplomacy
COPY variants variants
COPY front/game-board/dist/game-board.min.js nudiplomacy/static/gboard/game-board.js
COPY front/game-board/dist/tw.min.css nudiplomacy/static/gboard/tw.css
