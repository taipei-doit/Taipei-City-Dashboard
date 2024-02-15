// Package cmd provides the command line interface for the application.
package cmd

import (
	"fmt"
	"os"

	"TaipeiCityDashboardBE/internal/app"
	"TaipeiCityDashboardBE/logs"

	"github.com/spf13/cobra"
)

// rootCmd represents the root command for the TaipeiCityDashboardBE application.
var rootCmd = &cobra.Command{
	Use:   "TaipeiCityDashboardBE",
	Short: "Taipei Dashboard application backend",
	Long:  "Backend application for APIs and account management.",
	Run: func(cmd *cobra.Command, args []string) {
		logs.Info("Welcome to Dashboard Backend!")
		// Start the application when the root command is executed.
		app.StartApplication()
	},
}

// // checkExpiredCmd represents the command to check and disable expired accounts.
//
//	var checkExpiredCmd = &cobra.Command{
//		Use:   "checkExpired",
//		Short: "disable expired account",
//		Long:  "Check expired account and disable it.",
//		Run: func(cmd *cobra.Command, args []string) {
//			// Start the process of checking and disabling expired accounts.
//			auth.CheckExpired()
//		},
//	}
//

// checkExpiredCmd represents the command to check and disable expired accounts.
var migrateDBCmd = &cobra.Command{
	Use:   "migrateDB",
	Short: "create or update DB Schema",
	Long:  "Use models paclage to Create or Update manager DB table Schema.",
	Run: func(cmd *cobra.Command, args []string) {
		logs.Info("Start the process of migrate manager database schema.")
		app.MigrateManagerSchema()
	},
}

// Execute initializes Cobra and adds the checkExpiredCmd to the root command.
func Execute() {
	rootCmd.AddCommand(migrateDBCmd)
	// Execute the root command and handle any errors.
	if err := rootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
