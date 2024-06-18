package controllers

import (
	"fmt"
	"net/http"

	"github.com/gin-gonic/gin"
	"golang.org/x/net/websocket"
)

var clients = make(map[*websocket.Conn]bool) // Connected clients

func ServeWs(c *gin.Context) {
	var (
		w http.ResponseWriter
		r *http.Request
	)
	w, r = c.Writer, c.Request
	// Upgrade the HTTP connection to a WebSocket connection
	wsHandler := websocket.Handler(func(ws *websocket.Conn) {
		defer func () {
			ws.Close()
			delete(clients, ws)
		}()

		// Add client to the clients map
		clients[ws] = true

		// WebSocket connection established
		for {
			var msg string
			// Read message from client
			err := websocket.Message.Receive(ws, &msg)
			if err != nil {
				// Handle error
				fmt.Println("Read message error: ", err)
				break
			}
			// Print message received from client
			fmt.Printf("Received message: %s\n", msg)

			// Broadcast message to all connected clients
			for client := range clients {
				err := websocket.Message.Send(client, msg)
				if err != nil {
						// Handle error
						fmt.Println("Client ", client, " Error :" ,err)
						break
				}
			}
		}
	})

	// Serve WebSocket requests
	wsHandler.ServeHTTP(w, r)
}