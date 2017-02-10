package main

// Written by: Jakub Moscicki, CERN IT, Feb 2017
// License: AGPL

/* Simple hey-you test server on port 8080. 

Use "hey" to talk to "you".

"hey": github.com/rakyll/hey

Requests:
GET /x   : wait x ms to return response
GET /mean/stdev : wait mean +-v stdev to return response
 
// prep: 

export GOPATH=~/go
export PATH=/usr/localgo/bin:$PATH
cd ~/go/src
git clone https://github.com/cernbox/smashbox.git

// usage: 

$ go install smashbox/performance/you && ~/go/bin/you &
Started...

$ curl http://localhost:8080/1000
#Wait, 1000000000ms URI /1000
2017-02-10 13:30:31.328531997 +0100 CET
2017-02-10 13:30:32.341854633 +0100 CET

$ go get github.com/rakyll/hey

$ hey http://localhost:8080/1000/500

11 requests done.
23 requests done.
58 requests done.
87 requests done.
112 requests done.
137 requests done.
153 requests done.
174 requests done.
182 requests done.
192 requests done.
198 requests done.
199 requests done.
All requests done.

Summary:
  Total:	6.3270 secs
  Slowest:	2.3662 secs
  Fastest:	0.0004 secs
  Average:	0.9576 secs
  Requests/sec:	31.6105
  Total data:	22049 bytes
  Size/request:	110 bytes

Status code distribution:
  [200]	200 responses

Response time histogram:
  0.000 [1]	|∎
  0.237 [16]	|∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎
  0.474 [24]	|∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎
  0.710 [28]	|∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎
  0.947 [20]	|∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎
  1.183 [42]	|∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎
  1.420 [33]	|∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎
  1.656 [17]	|∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎
  1.893 [10]	|∎∎∎∎∎∎∎∎∎∎
  2.130 [5]	|∎∎∎∎∎
  2.366 [4]	|∎∎∎∎

Latency distribution:
  10% in 0.2612 secs
  25% in 0.5534 secs
  50% in 1.0034 secs
  75% in 1.3182 secs
  90% in 1.6062 secs
  95% in 1.8917 secs
  99% in 2.2673 secs



*/

import (
	"fmt"
	"net/http"
	"log"
	"time"
	"strconv"
	"math/rand"
	"strings"
)

func waitHandler(writer http.ResponseWriter, request *http.Request) {

	s := strings.Split(request.URL.Path[1:],"/")

	wait,err := strconv.Atoi(s[0])
	wait = wait*1000000
	if err != nil {
		fmt.Fprintf(writer,"error %s",err)
	}

	
	if len(s) > 1 {
		stddev,err := strconv.Atoi(s[1])
		stddev = stddev*1000000
		if err != nil {
			fmt.Fprintf(writer,"error %s",err)
		}
		wait += int(rand.NormFloat64() * float64(stddev))
	}
	
	fmt.Fprintf(writer, "Wait, %d URI %s\n", wait, request.URL.Path)
	fmt.Fprintf(writer, "%s\n", time.Now())
	time.Sleep(time.Duration(wait))
	fmt.Fprintf(writer, "%s\n", time.Now())

	fmt.Printf("#")
}

func main() {

	fmt.Printf("Started...\n")
	
	http.HandleFunc("/", waitHandler)

	//log.Fatal(http.ListenAndServeTLS(":443", "server.crt", "server.key", nil))
	log.Fatal(http.ListenAndServe(":8080", nil))
}
