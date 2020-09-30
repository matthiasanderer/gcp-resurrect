#!/bin/bash
# -*- coding: utf-8 -*-

# Original version: https://github.com/itamaro/gcp-night-king/blob/master/zombie.sh

META_URL="http://metadata.google.internal/computeMetadata/v1/instance"
GCLOUD=gcloud
TOPIC="prere"
get_meta() {
  curl -s "$META_URL/$1" -H "Metadata-Flavor: Google"
}
IS_PREEMPTED="$( get_meta preempted )"
if [ "$IS_PREEMPTED" == "TRUE" ]; then
  NAME="$( get_meta name )"
  ZONE="$( get_meta zone | cut -d '/' -f 4 )"
  "$GCLOUD" pubsub topics publish "$TOPIC" \
      --message '{"name": "'${NAME}'", "zone": "'${ZONE}'"}'
fi
