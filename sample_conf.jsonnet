{
	"mipmip.task.cat_sample_file": {
		target: "cat",
		args: {
			"positional": ["sample_text_file"]
		},
		"artifacts": {
			"stdout": {
				"type": "stdout",
			},
		},
	},
	"mipmip.task.echo": {
		target: "echo",
		"args": {
			"positional": [
				"mipmip.artifacts.cat_sample_file.stdout",
				"apples",
				"oranges",
				[
					"XXX",
					"YYY"
				]
			],
			"named": {
				"--grocery_list": ["apples", "oranges"],
				"--grocery_list_2": ["apples", "oranges"],
				"--grocery_list_3": {
					"apples": "1",
					"oranges": "2"
				},
				"--grocery_list_4": {
					"apples": {
						"green": "1",
						"red": "2"
					},
					"oranges": "2"
				}
			}
		}
	},
	"mipmip.arg_policy.echo": {
		"positional": {
			"5": {
				"glue": ":"
			}
		},
		"named": {
			"--grocery_list_2": {
				"glue": "|"
			},
			"--grocery_list_3": {
				"glue": "/",
				"inner_glue": ":"
			},
			"--grocery_list_4": {
				"glue": " ",
				"inner_glue": ":",
				"wrap": "\""
			}
		}
	},
	"mipmip.workflow.echo2": {
		"tasks": [
			"cat_sample_file",
			"echo"
		]
	},
}

