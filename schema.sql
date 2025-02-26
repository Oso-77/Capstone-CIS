-- Table Schema
CREATE TABLE `feedback` (
  `entryID` int(11) NOT NULL AUTO_INCREMENT,
  `feedback` enum('thumbs_up','thumbs_down','thumbs_middle') NOT NULL,
  `comment1` varchar(150) DEFAULT NULL,
  `comment2` varchar(150) DEFAULT NULL,
  `comment3` varchar(150) DEFAULT NULL,
  `gpt_answer_1` text DEFAULT NULL,
  `gpt_answer_2` text DEFAULT NULL,
  `gpt_answer_3` text DEFAULT NULL,
  `received_at` date NOT NULL DEFAULT (curdate()),
  `survey_category` enum('Work Environment','Job Satisfaction','Management/Leadership','Tools/Technology','Training/Development','Processes/Procedures','Invalid') NOT NULL,
  `cards_generated` tinyint(4) DEFAULT 0,
  `leader_response` text DEFAULT NULL,
  PRIMARY KEY (`entryID`)
) ENGINE=InnoDB AUTO_INCREMENT=83 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

CREATE TABLE `posts` (
  `post_id` int(11) NOT NULL AUTO_INCREMENT,
  `db_id` int(11) NOT NULL,
  `post_title` varchar(255) NOT NULL,
  `post_body` text NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`post_id`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

CREATE TABLE `responses` (
  `db_id` int(11) NOT NULL AUTO_INCREMENT,
  `response_text` text NOT NULL,
  `received_at` date DEFAULT (curdate()),
  `insight_text` text DEFAULT NULL,
  `survey_category` enum('Work Environment','Job Satisfaction','Management/Leadership','Tools/Technology','Training/Development','Processes/Procedures','Invalid') NOT NULL,
  `leader_feedback` text DEFAULT NULL,
  PRIMARY KEY (`db_id`)
) ENGINE=InnoDB AUTO_INCREMENT=388 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

CREATE TABLE `users` (
  `UserID` int(11) NOT NULL AUTO_INCREMENT,
  `UserUN` varchar(80) NOT NULL,
  `UserPW` varchar(80) NOT NULL,
  `isAdmin` tinyint(4) NOT NULL,
  PRIMARY KEY (`UserID`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- Account Creation Sample Query
INSERT INTO users (UserUN, UserPW, isAdmin)
values
('adminuser', '[hashed_password]', 1),
('reguser', '[hashed_password]', 0);
-- Passwords can be hashed with "hashPassword.js" within middleware folder 
-- Change const plainTextPassword to desired password, run script, insert password into table following above query