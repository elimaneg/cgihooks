#!/bin/bash

# This code for getting code from post data is from http://oinkzwurgl.org/bash_cgi and 
# was written by Phillippe Kehi <phkehi@gmx.net> and flipflip industries 
# elimane.gueye@gmail : process gitlab system hook
# http://stedolan.github.io/jq/download/linux64/jq

JQ=jq
# (internal) routine to store POST data 
function cgi_get_POST_vars() { 
 # check content type 
 #[ "${CONTENT_TYPE}" != "application/x-www-form-urlencoded" ] && \
 #echo "Warning: you should probably use MIME type "\ "application/x-www-form-urlencoded!" 1>&2 
 # save POST variables (only first time this is called) 
 #echo "QUERY_STRING_POST = $QUERY_STRING_POST" 1>&2
 #echo "REQUEST_METHOD = $REQUEST_METHOD" 1>&2
 #echo "CONTENT_LENGTH = $CONTENT_LENGTH" 1>&2
 [ -z "$QUERY_STRING_POST" -a "$REQUEST_METHOD" = "POST" -a ! -z "$CONTENT_LENGTH" ] && \
 read -n $CONTENT_LENGTH QUERY_STRING_POST 
 return 
} 

# (internal) routine to decode urlencoded strings
function cgi_decodevar() { 
 [ $# -ne 1 ] && return 
 local v t h 
 # replace all + with whitespace and append %% 
 t="${1//+/ }%%" 
 while [ ${#t} -gt 0 -a "${t}" != "%" ]; do 
  v="${v}${t%%\%*}" 
  # digest up to the first % 
  t="${t#*%}" 
  # remove digested part 
  # decode if there is anything to decode and if not at end of string 
  if [ ${#t} -gt 0 -a "${t}" != "%" ]; then 
    h=${t:0:2} 
    # save first two chars 
    t="${t:2}" 
    # remove these 
    v="${v}"`echo -e \\\\x${h}` 
    # convert hex to special char 
  fi 
 done 
 # return decoded string 
 echo "${v}" 
 return 
} 


# routine to get variables from http requests 
# usage: cgi_getvars method varname1 [.. varnameN] 
# method is either GET or POST or BOTH 
# the magic varible name ALL gets everything 

function cgi_getvars() { 
 [ $# -lt 2 ] && return 
 local q p k v s 
 # get query 
 echo "XXX : $1"
 case $1 in 
      GET) [ ! -z "${QUERY_STRING}" ] && q="${QUERY_STRING}&" ;; 
      POST) cgi_get_POST_vars 
            [ ! -z "${QUERY_STRING_POST}" ] && q="${QUERY_STRING_POST}&" ;; 
      BOTH) [ ! -z "${QUERY_STRING}" ] && q="${QUERY_STRING}&" 
            cgi_get_POST_vars 
            [ ! -z "${QUERY_STRING_POST}" ] && q="${q}${QUERY_STRING_POST}&" ;; 
 esac 
 shift 
 s=" $* " 
 # parse the query data 
 while [ ! -z "$q" ]; do 
   p="${q%%&*}"  # get first part of query string 
   k="${p%%=*}"  # get the key (variable name) from it 
   v="${p#*=}"   # get the value from it 
   q="${q#$p&*}" # strip first part from query string 
   # decode and evaluate var if requested 
   #[ "$1" = "ALL" -o "${s/ $k /}" != "$s" ] && eval "$k=\"`cgi_decodevar \"$v\"`\"" 
   #[ "$1" = "ALL" -o "${s/ $k /}" != "$s" ] && echo "Cle = $q" 1>&2 && echo "Valeur = $v" 1>&2
 done 
 _SERVER=localhost
 _EVENT=$(echo $v|jq -r '.event_name')
 _PROJECT=$(echo $v|jq -r '.name' |sed "s/\"//g")
 _NAMESPACE=$(echo $v|jq -r '.path_with_namespace')
 _EMAIL=$(echo $v|jq -r '.owner_email')
 _OWNER=$(echo $v|jq -r '.owner_name')
 _VISIBILITY=$(echo $v|jq -r '.project_visibility')
 _REPOS=git@${_SERVER}:${_NAMESPACE}.git
 _REPOS_HTTP=http://${_SERVER}/${_NAMESPACE}.git
 _LOG="Event=${_EVENT}, PROJECT=${_PROJECT}, NAMESPACE=${_NAMESPACE}, OWNER=${_OWNER}, EMAIL=${_OWNER}, REPOS=${_REPOS}, REPOS_HTTP=${_REPOS_HTTP}"
 _REQ=$( echo $v|jq -r '.' )
 # {"event_name":"project_create","created_at":"2015-02-12T02:15:21Z","name":"test_cgi","path":"test_cgi","path_with_namespace":"ege/test_cgi","project_id":12,"owner_name":"Elimane","owner_email":"ege@gmail.com","project_visibility":"internal"}
 case ${_EVENT}  in
    project_create)
         create_job ${_PROJECT};;
    project_destroy)
         remove_job ${_PROJECT};;
   *)
    echo $_LOG 1>&2
    echo $_REQ 1>&2
 esac
 # if project_destroy
 #{"event_name":"project_destroy","created_at":"2015-02-12T02:06:55Z","name":"projet_test","path":"projet_test","path_with_namespace":"core/projet_test","project_id":10,"owner_name":"core","owner_email":null,"project_visibility":"private"}

 echo "Status: 200 OK"
 echo "Content-type: text/html"
 echo
 echo  "<html><head><meta charset=UTF-8><title>System Hook</title></head><body>Success</body></html>"
  
return 
}

# pour recuperer les variables d'env du serveur dans les logs d'erreurs
#env 1>&2 
cgi_getvars POST ALL
