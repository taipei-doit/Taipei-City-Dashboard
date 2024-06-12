// Package logs provides logging for the application.
/*
Developed By Taipei Urban Intelligence Center 2023-2024

// Lead Developer:  Igor Ho (Full Stack Engineer)
// Systems & Auth: Ann Shih (Systems Engineer)
// Data Pipelines:  Iima Yu (Data Scientist)
// Design and UX: Roy Lin (Prev. Consultant), Chu Chen (Researcher)
// Testing: Jack Huang (Data Scientist), Ian Huang (Data Analysis Intern)
*/
package logs

import (
	"fmt"
	"log"
	"runtime"
	"strconv"

	"github.com/comail/colog"
)

func init() {
	colog.SetFormatter(&colog.StdFormatter{
		Colors: true,
		Flag:   log.Ltime, /*| log.Lshortfile*/
	})
	colog.Register()
	colog.SetMinLevel(colog.LInfo)
	colog.SetDefaultLevel(colog.LInfo)
	colog.ParseFields(false)
}

// Trace is used to print trace level message
func Trace(v ...interface{}) {
	log.Println("t:", getFileLine(), fmt.Sprintln(v...))
}

// Debug is used to print debug level message
func Debug(v ...interface{}) {
	log.Println("d:", getFileLine(), fmt.Sprintln(v...))
}

// Info is used to print info level message
func Info(v ...interface{}) {
	log.Println("i:", getFileLine(), fmt.Sprintln(v...))
}

// Warn is used to print warning level message
func Warn(v ...interface{}) {
	log.Println("w:", getFileLine(), fmt.Sprintln(v...))
}

// Error is used to print error level message
func Error(v ...interface{}) {
	log.Println("e:", getFileLine(), fmt.Sprintln(v...))
}

// Alert is used to print alert level message
func Alert(v ...interface{}) {
	log.Println("alert:", getFileLine(), fmt.Sprintln(v...))
}

// FTrace is used to print trace level message with format
func FTrace(format string, v ...interface{}) {
	log.Println("t:", getFileLine(), fmt.Sprintf(format, v...))
}

// FDebug is used to print debug level message with format
func FDebug(format string, v ...interface{}) {
	log.Println("d:", getFileLine(), fmt.Sprintf(format, v...))
}

// FInfo is used to print info level message with format
func FInfo(format string, v ...interface{}) {
	log.Println("i:", getFileLine(), fmt.Sprintf(format, v...))
}

// FWarn is used to print warning level message with format
func FWarn(format string, v ...interface{}) {
	log.Println("w:", getFileLine(), fmt.Sprintf(format, v...))
}

// FError is used to print error level message with format
func FError(format string, v ...interface{}) {
	log.Println("e:", getFileLine(), fmt.Sprintf(format, v...))
}

// FAlert is used to print alert level message with format
func FAlert(format string, v ...interface{}) {
	log.Println("alert:", getFileLine(), fmt.Sprintf(format, v...))
}

// get file a line where logger was called
func getFileLine() string {
	var fileln string
	var file string
	var line int
	var ok bool

	_, file, line, ok = runtime.Caller(2)
	if ok {
		short := file
		for i := len(file) - 1; i > 0; i-- {
			if file[i] == '/' {
				short = file[i+1:]
				break
			}
		}
		file = short
	} else {
		file = "???"
		line = 0
	}
	fileln = "(" + file + ":" + strconv.Itoa(line) + ")"
	return fileln
}
