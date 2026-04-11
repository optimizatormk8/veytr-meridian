#!/usr/bin/env bash
set -euo pipefail

mkdir -p tests/systemlab/ca tests/systemlab/output/camouflage

if [ ! -f tests/systemlab/ca/rootCA.key ]; then
  openssl genrsa -out tests/systemlab/ca/rootCA.key 2048 >/dev/null 2>&1
  openssl req -x509 -new -nodes -key tests/systemlab/ca/rootCA.key -sha256 -days 3650 \
    -subj '/CN=Meridian System Lab Root CA' \
    -out tests/systemlab/ca/rootCA.pem >/dev/null 2>&1
fi

cat > tests/systemlab/output/camouflage/openssl.cnf <<'CNF'
[ req ]
default_bits       = 2048
prompt             = no
default_md         = sha256
distinguished_name = req_dn
req_extensions     = req_ext

[ req_dn ]
CN = camouflage.test

[ req_ext ]
subjectAltName = @alt_names

[ alt_names ]
DNS.1 = camouflage.test
CNF

openssl genrsa -out tests/systemlab/output/camouflage/server.key 2048 >/dev/null 2>&1
openssl req -new -key tests/systemlab/output/camouflage/server.key \
  -out tests/systemlab/output/camouflage/server.csr \
  -config tests/systemlab/output/camouflage/openssl.cnf >/dev/null 2>&1
openssl x509 -req -in tests/systemlab/output/camouflage/server.csr \
  -CA tests/systemlab/ca/rootCA.pem -CAkey tests/systemlab/ca/rootCA.key -CAcreateserial \
  -out tests/systemlab/output/camouflage/server.crt -days 365 -sha256 \
  -extensions req_ext -extfile tests/systemlab/output/camouflage/openssl.cnf >/dev/null 2>&1
cp tests/systemlab/output/camouflage/server.crt tests/systemlab/output/camouflage/fullchain.pem
