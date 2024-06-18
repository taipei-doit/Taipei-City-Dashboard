// Package cmd provides the command line interface for the application.
/*
Developed By Taipei Urban Intelligence Center 2023-2024

// Lead Developer:  Igor Ho (Full Stack Engineer)
// Systems & Auth: Ann Shih (Systems Engineer)
// Data Pipelines:  Iima Yu (Data Scientist)
// Design and UX: Roy Lin (Prev. Consultant), Chu Chen (Researcher)
// Testing: Jack Huang (Data Scientist), Ian Huang (Data Analysis Intern)
*/
package cmd

import (
	"fmt"
	"os"

	"TaipeiCityDashboardBE/app"
	"TaipeiCityDashboardBE/logs"

	"github.com/spf13/cobra"
)

// rootCmd represents the root command for the TaipeiCityDashboardBE application.
var rootCmd = &cobra.Command{
	Use:   "TaipeiCityDashboardBE",
	Short: "Taipei Dashboard application backend",
	Long:  "Backend application for APIs and account management.",
	Run: func(_ *cobra.Command, _ []string) {
		logs.Info("Welcome to Dashboard Backend!")
		// Start the application when the root command is executed.
		app.StartApplication()
	},
}

// migrateDBCmd
var migrateDBCmd = &cobra.Command{
	Use:   "migrateDB",
	Short: "create or update DB Schema",
	Long:  "Use models paclage to Create or Update manager DB table Schema.",
	Run: func(_ *cobra.Command, _ []string) {
		logs.Info("Start the process of migrate manager database schema.")
		app.MigrateManagerSchema()
	},
}

// initDashboardDBCmd
var initDashboardDBCmd = &cobra.Command{
	Use:   "initDashboard",
	Short: "init Dashboatd data",
	Long:  "init Dashboatd data.",
	Run: func(_ *cobra.Command, _ []string) {
		logs.Info("Start the process of insert dashboard database data.")
		app.InsertDashbaordSampleData()
	},
}

// Execute initializes Cobra and adds the checkExpiredCmd to the root command.
func Execute() {
	rootCmd.AddCommand(migrateDBCmd)
	rootCmd.AddCommand(initDashboardDBCmd)
	// Execute the root command and handle any errors.
	if err := rootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
