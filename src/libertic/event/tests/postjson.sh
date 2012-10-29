#!/usr/bin/env bash
B="http://localhost:30013/Plone/fr"
case $1 in
    c)
        curl -v  -u admin:secret -X POST \
            -H "Accept: application/json" \
            -H "Content-type: application/json" \
            -d '{"events": [ {} ]}' \
            $B/database/json_api > ~/.json.html
        ;;
esac
#curl -v -u admin:secret $B  > ~/.json.html
# vim:set et sts=4 ts=4 tw=0:
