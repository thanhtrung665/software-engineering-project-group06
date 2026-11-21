-- MySQL 8.4 schema generated from Section VI (40 detailed tables) of Hotel_Booking_System_Group06(3).docx.
-- Review and run on a fresh schema. Uses InnoDB, utf8mb4 and MySQL-compatible types.
CREATE DATABASE IF NOT EXISTS `hotel_booking_system` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `hotel_booking_system`;
SET FOREIGN_KEY_CHECKS=0;
CREATE TABLE IF NOT EXISTS `role` (
  `role_id` BIGINT NOT NULL AUTO_INCREMENT,
  `role_code` VARCHAR(30) NOT NULL,
  `role_name` VARCHAR(100) NOT NULL,
  `description` VARCHAR(255) NULL,
  UNIQUE KEY `uq_role_role_code` (`role_code`),
  PRIMARY KEY (`role_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `account` (
  `account_id` BIGINT NOT NULL AUTO_INCREMENT,
  `role_id` BIGINT NOT NULL,
  `full_name` VARCHAR(150) NOT NULL,
  `email` VARCHAR(254) NOT NULL,
  `phone` VARCHAR(20) NOT NULL,
  `nationality` VARCHAR(80) NULL,
  `password_hash` VARCHAR(255) NULL,
  `account_status` VARCHAR(20) NOT NULL,
  `failed_login_count` SMALLINT NOT NULL DEFAULT 0,
  `login_locked_until` DATETIME(6) NULL,
  `locked_reason` VARCHAR(500) NULL,
  `locked_until` DATETIME(6) NULL,
  `privacy_consent_at` DATETIME(6) NULL,
  `created_at` DATETIME(6) NOT NULL,
  `updated_at` DATETIME(6) NOT NULL,
  `deleted_at` DATETIME(6) NULL,
  PRIMARY KEY (`account_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `account_session` (
  `session_id` CHAR(36) NOT NULL,
  `account_id` BIGINT NOT NULL,
  `session_token_hash` VARCHAR(255) NOT NULL,
  `created_at` DATETIME(6) NOT NULL,
  `last_activity_at` DATETIME(6) NOT NULL,
  `expires_at` DATETIME(6) NOT NULL,
  `revoked_at` DATETIME(6) NULL,
  PRIMARY KEY (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `auth_token` (
  `auth_token_id` BIGINT NOT NULL AUTO_INCREMENT,
  `account_id` BIGINT NOT NULL,
  `token_hash` VARCHAR(255) NOT NULL,
  `token_type` VARCHAR(20) NOT NULL,
  `created_at` DATETIME(6) NOT NULL,
  `expires_at` DATETIME(6) NOT NULL,
  `used_at` DATETIME(6) NULL,
  `revoked_at` DATETIME(6) NULL,
  PRIMARY KEY (`auth_token_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `hotel` (
  `hotel_id` BIGINT NOT NULL AUTO_INCREMENT,
  `star_rating` TINYINT NOT NULL,
  `address` VARCHAR(500) NOT NULL,
  `latitude` DECIMAL(10,7) NULL,
  `longitude` DECIMAL(10,7) NULL,
  `hotline` VARCHAR(30) NOT NULL,
  `contact_email` VARCHAR(254) NOT NULL,
  `created_at` DATETIME(6) NOT NULL,
  `updated_at` DATETIME(6) NOT NULL,
  PRIMARY KEY (`hotel_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `hotel_translation` (
  `hotel_translation_id` BIGINT NOT NULL AUTO_INCREMENT,
  `hotel_id` BIGINT NOT NULL,
  `language_code` CHAR(2) NOT NULL,
  `hotel_name` VARCHAR(200) NOT NULL,
  `description` TEXT NOT NULL,
  UNIQUE KEY `uq_hotel_translation_1` (`hotel_id`, `language_code`),
  PRIMARY KEY (`hotel_translation_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `hotel_image` (
  `hotel_image_id` BIGINT NOT NULL AUTO_INCREMENT,
  `hotel_id` BIGINT NOT NULL,
  `image_url` VARCHAR(1000) NOT NULL,
  `alt_text` VARCHAR(255) NULL,
  `display_order` INT NOT NULL DEFAULT 0,
  `is_primary` TINYINT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`hotel_image_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `amenity` (
  `amenity_id` BIGINT NOT NULL AUTO_INCREMENT,
  `amenity_code` VARCHAR(50) NOT NULL,
  `amenity_scope` VARCHAR(20) NOT NULL,
  `created_at` DATETIME(6) NOT NULL,
  PRIMARY KEY (`amenity_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `amenity_translation` (
  `amenity_translation_id` BIGINT NOT NULL AUTO_INCREMENT,
  `amenity_id` BIGINT NOT NULL,
  `language_code` CHAR(2) NOT NULL,
  `amenity_name` VARCHAR(120) NOT NULL,
  UNIQUE KEY `uq_amenity_translation_1` (`amenity_id`, `language_code`),
  PRIMARY KEY (`amenity_translation_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `hotel_amenity` (
  `hotel_id` BIGINT NOT NULL,
  `amenity_id` BIGINT NOT NULL,
  PRIMARY KEY (`hotel_id`, `amenity_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `hotel_policy` (
  `policy_id` BIGINT NOT NULL AUTO_INCREMENT,
  `hotel_id` BIGINT NOT NULL,
  `policy_code` VARCHAR(50) NOT NULL,
  `language_code` CHAR(2) NOT NULL,
  `policy_title` VARCHAR(200) NOT NULL,
  `policy_content` TEXT NOT NULL,
  `effective_from` DATE NOT NULL,
  `effective_to` DATE NULL,
  PRIMARY KEY (`policy_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `room_type` (
  `room_type_id` BIGINT NOT NULL AUTO_INCREMENT,
  `hotel_id` BIGINT NOT NULL,
  `room_type_code` VARCHAR(30) NOT NULL,
  `area_sqm` DECIMAL(7,2) NOT NULL,
  `bed_type` VARCHAR(30) NOT NULL,
  `max_adults` SMALLINT NOT NULL,
  `max_children` SMALLINT NOT NULL DEFAULT 0,
  `view_direction` VARCHAR(50) NULL,
  `breakfast_included` TINYINT(1) NOT NULL DEFAULT 0,
  `base_price` DECIMAL(14,2) NOT NULL,
  `selling_status` VARCHAR(20) NOT NULL,
  `created_at` DATETIME(6) NOT NULL,
  `updated_at` DATETIME(6) NOT NULL,
  PRIMARY KEY (`room_type_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `room_type_translation` (
  `room_type_translation_id` BIGINT NOT NULL AUTO_INCREMENT,
  `room_type_id` BIGINT NOT NULL,
  `language_code` CHAR(2) NOT NULL,
  `room_type_name` VARCHAR(120) NOT NULL,
  `description` TEXT NOT NULL,
  `view_label` VARCHAR(120) NULL,
  UNIQUE KEY `uq_room_type_translation_1` (`room_type_id`, `language_code`),
  PRIMARY KEY (`room_type_translation_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `room_type_image` (
  `room_type_image_id` BIGINT NOT NULL AUTO_INCREMENT,
  `room_type_id` BIGINT NOT NULL,
  `image_url` VARCHAR(1000) NOT NULL,
  `alt_text` VARCHAR(255) NULL,
  `display_order` INT NOT NULL DEFAULT 0,
  `is_primary` TINYINT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`room_type_image_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `room_type_amenity` (
  `room_type_id` BIGINT NOT NULL,
  `amenity_id` BIGINT NOT NULL,
  PRIMARY KEY (`room_type_id`, `amenity_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `room` (
  `room_id` BIGINT NOT NULL AUTO_INCREMENT,
  `room_type_id` BIGINT NOT NULL,
  `room_number` VARCHAR(20) NOT NULL,
  `floor_number` SMALLINT NOT NULL,
  `room_status` VARCHAR(20) NOT NULL,
  `is_active` TINYINT(1) NOT NULL DEFAULT 1,
  `created_at` DATETIME(6) NOT NULL,
  `updated_at` DATETIME(6) NOT NULL,
  PRIMARY KEY (`room_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `room_maintenance` (
  `maintenance_id` BIGINT NOT NULL AUTO_INCREMENT,
  `room_id` BIGINT NOT NULL,
  `start_date` DATE NOT NULL,
  `end_date` DATE NOT NULL,
  `reason` VARCHAR(500) NOT NULL,
  `maintenance_status` VARCHAR(20) NOT NULL,
  `created_by` BIGINT NOT NULL,
  `created_at` DATETIME(6) NOT NULL,
  PRIMARY KEY (`maintenance_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `room_rate` (
  `room_rate_id` BIGINT NOT NULL AUTO_INCREMENT,
  `room_type_id` BIGINT NOT NULL,
  `rate_type` VARCHAR(20) NOT NULL,
  `start_date` DATE NULL,
  `end_date` DATE NULL,
  `weekday_no` SMALLINT NULL,
  `nightly_price` DECIMAL(14,2) NOT NULL,
  `is_active` TINYINT(1) NOT NULL DEFAULT 1,
  `created_by` BIGINT NOT NULL,
  `created_at` DATETIME(6) NOT NULL,
  PRIMARY KEY (`room_rate_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `holiday_date` (
  `holiday_date_id` BIGINT NOT NULL AUTO_INCREMENT,
  `holiday_date` DATE NOT NULL,
  `holiday_name` VARCHAR(120) NOT NULL,
  `is_active` TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`holiday_date_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `room_rate_holiday` (
  `room_rate_id` BIGINT NOT NULL,
  `holiday_date_id` BIGINT NOT NULL,
  PRIMARY KEY (`room_rate_id`, `holiday_date_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `deposit_level` (
  `deposit_level_id` BIGINT NOT NULL AUTO_INCREMENT,
  `percentage` DECIMAL(5,2) NOT NULL,
  `is_active` TINYINT(1) NOT NULL DEFAULT 1,
  `effective_from` DATETIME(6) NOT NULL,
  `effective_to` DATETIME(6) NULL,
  `updated_by` BIGINT NOT NULL,
  PRIMARY KEY (`deposit_level_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `promotion` (
  `promotion_id` BIGINT NOT NULL AUTO_INCREMENT,
  `promo_code` VARCHAR(40) NOT NULL,
  `discount_type` VARCHAR(10) NOT NULL,
  `discount_value` DECIMAL(14,2) NOT NULL,
  `max_discount` DECIMAL(14,2) NULL,
  `min_nights` SMALLINT NOT NULL DEFAULT 1,
  `min_order_value` DECIMAL(14,2) NOT NULL DEFAULT 0,
  `valid_from` DATETIME(6) NOT NULL,
  `valid_to` DATETIME(6) NOT NULL,
  `total_usage_limit` INT NULL,
  `per_account_limit` INT NOT NULL,
  `used_count` INT NOT NULL DEFAULT 0,
  `promotion_status` VARCHAR(15) NOT NULL,
  `is_public` TINYINT(1) NOT NULL DEFAULT 0,
  `created_by` BIGINT NOT NULL,
  `created_at` DATETIME(6) NOT NULL,
  PRIMARY KEY (`promotion_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `promotion_room_type` (
  `promotion_id` BIGINT NOT NULL,
  `room_type_id` BIGINT NOT NULL,
  PRIMARY KEY (`promotion_id`, `room_type_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `promotion_redemption` (
  `redemption_id` BIGINT NOT NULL AUTO_INCREMENT,
  `promotion_id` BIGINT NOT NULL,
  `account_id` BIGINT NOT NULL,
  `booking_id` BIGINT NOT NULL,
  `discount_amount` DECIMAL(14,2) NOT NULL,
  `redeemed_at` DATETIME(6) NOT NULL,
  `redemption_status` VARCHAR(15) NOT NULL,
  PRIMARY KEY (`redemption_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `booking` (
  `booking_id` BIGINT NOT NULL AUTO_INCREMENT,
  `booking_code` VARCHAR(30) NOT NULL,
  `account_id` BIGINT NULL,
  `created_by` BIGINT NULL,
  `booking_source` VARCHAR(15) NOT NULL,
  `check_in_date` DATE NOT NULL,
  `check_out_date` DATE NOT NULL,
  `adults` SMALLINT NOT NULL,
  `children` SMALLINT NOT NULL DEFAULT 0,
  `room_count` SMALLINT NOT NULL,
  `guest_contact_name` VARCHAR(150) NOT NULL,
  `guest_contact_phone` VARCHAR(20) NOT NULL,
  `guest_contact_email` VARCHAR(254) NULL,
  `special_requests` TEXT NULL,
  `estimated_arrival_time` TIME NULL,
  `booking_status` VARCHAR(25) NOT NULL,
  `payment_status` VARCHAR(25) NOT NULL,
  `currency` CHAR(3) NOT NULL DEFAULT 'VND',
  `subtotal_amount` DECIMAL(14,2) NOT NULL,
  `discount_amount` DECIMAL(14,2) NOT NULL DEFAULT 0,
  `total_amount` DECIMAL(14,2) NOT NULL,
  `deposit_percentage` DECIMAL(5,2) NOT NULL,
  `deposit_amount` DECIMAL(14,2) NOT NULL,
  `paid_amount` DECIMAL(14,2) NOT NULL DEFAULT 0,
  `remaining_amount` DECIMAL(14,2) NOT NULL,
  `hold_expires_at` DATETIME(6) NULL,
  `policy_snapshot` JSON NOT NULL,
  `terms_accepted_at` DATETIME(6) NOT NULL,
  `cancelled_at` DATETIME(6) NULL,
  `cancellation_reason` VARCHAR(500) NULL,
  `created_at` DATETIME(6) NOT NULL,
  `updated_at` DATETIME(6) NOT NULL,
  PRIMARY KEY (`booking_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `booking_item` (
  `booking_item_id` BIGINT NOT NULL AUTO_INCREMENT,
  `booking_id` BIGINT NOT NULL,
  `room_type_id` BIGINT NOT NULL,
  `quantity` SMALLINT NOT NULL,
  `adults` SMALLINT NOT NULL,
  `children` SMALLINT NOT NULL DEFAULT 0,
  `line_subtotal` DECIMAL(14,2) NOT NULL,
  `line_discount` DECIMAL(14,2) NOT NULL DEFAULT 0,
  `line_total` DECIMAL(14,2) NOT NULL,
  UNIQUE KEY `uq_booking_item_1` (`booking_id`, `room_type_id`),
  PRIMARY KEY (`booking_item_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `booking_night_rate` (
  `booking_night_rate_id` BIGINT NOT NULL AUTO_INCREMENT,
  `booking_item_id` BIGINT NOT NULL,
  `stay_date` DATE NOT NULL,
  `rate_type_applied` VARCHAR(20) NOT NULL,
  `source_room_rate_id` BIGINT NULL,
  `unit_price` DECIMAL(14,2) NOT NULL,
  `quantity` SMALLINT NOT NULL,
  `night_total` DECIMAL(14,2) NOT NULL,
  `night_discount` DECIMAL(14,2) NOT NULL DEFAULT 0,
  UNIQUE KEY `uq_booking_night_rate_1` (`booking_item_id`, `stay_date`),
  PRIMARY KEY (`booking_night_rate_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `booking_guest` (
  `booking_guest_id` BIGINT NOT NULL AUTO_INCREMENT,
  `booking_id` BIGINT NOT NULL,
  `assignment_id` BIGINT NULL,
  `full_name` VARCHAR(150) NOT NULL,
  `phone` VARCHAR(20) NULL,
  `nationality` VARCHAR(80) NULL,
  `document_type` VARCHAR(20) NULL,
  `document_number_encrypted` VARBINARY(512) NULL,
  `document_key_version` VARCHAR(30) NULL,
  `is_primary_guest` TINYINT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`booking_guest_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `booking_room_assignment` (
  `assignment_id` BIGINT NOT NULL AUTO_INCREMENT,
  `booking_item_id` BIGINT NOT NULL,
  `room_id` BIGINT NOT NULL,
  `assigned_at` DATETIME(6) NOT NULL,
  `released_at` DATETIME(6) NULL,
  `assigned_by` BIGINT NOT NULL,
  `is_upgrade` TINYINT(1) NOT NULL DEFAULT 0,
  `upgrade_reason` VARCHAR(500) NULL,
  PRIMARY KEY (`assignment_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `booking_status_history` (
  `booking_status_history_id` BIGINT NOT NULL AUTO_INCREMENT,
  `booking_id` BIGINT NOT NULL,
  `old_status` VARCHAR(25) NULL,
  `new_status` VARCHAR(25) NOT NULL,
  `changed_by` BIGINT NULL,
  `changed_source` VARCHAR(20) NOT NULL,
  `change_reason` VARCHAR(500) NULL,
  `changed_at` DATETIME(6) NOT NULL,
  PRIMARY KEY (`booking_status_history_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `payment` (
  `payment_id` BIGINT NOT NULL AUTO_INCREMENT,
  `booking_id` BIGINT NOT NULL,
  `payment_reference` VARCHAR(100) NOT NULL,
  `gateway_transaction_id` VARCHAR(150) NOT NULL,
  `payment_channel` VARCHAR(20) NOT NULL,
  `payment_method` VARCHAR(20) NOT NULL,
  `payment_purpose` VARCHAR(20) NOT NULL,
  `amount` DECIMAL(14,2) NOT NULL,
  `payment_status` VARCHAR(20) NOT NULL,
  `gateway_signature_valid` TINYINT(1) NULL,
  `gateway_payload_ref` VARCHAR(255) NULL,
  `processed_by` BIGINT NULL,
  `invoice_id` BIGINT NULL,
  `paid_at` DATETIME(6) NULL,
  `created_at` DATETIME(6) NOT NULL,
  PRIMARY KEY (`payment_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `refund` (
  `refund_id` BIGINT NOT NULL AUTO_INCREMENT,
  `booking_id` BIGINT NOT NULL,
  `payment_id` BIGINT NULL,
  `refund_reference` VARCHAR(100) NOT NULL,
  `refund_amount` DECIMAL(14,2) NOT NULL,
  `cancellation_fee` DECIMAL(14,2) NOT NULL DEFAULT 0,
  `refund_reason` VARCHAR(500) NOT NULL,
  `refund_type` VARCHAR(20) NOT NULL,
  `refund_channel` VARCHAR(15) NOT NULL,
  `refund_status` VARCHAR(20) NOT NULL,
  `gateway_refund_id` VARCHAR(150) NOT NULL,
  `processed_by` BIGINT NULL,
  `requested_at` DATETIME(6) NOT NULL,
  `completed_at` DATETIME(6) NULL,
  PRIMARY KEY (`refund_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `invoice` (
  `invoice_id` BIGINT NOT NULL AUTO_INCREMENT,
  `booking_id` BIGINT NOT NULL,
  `invoice_number` VARCHAR(50) NOT NULL,
  `issued_at` DATETIME(6) NOT NULL,
  `subtotal_amount` DECIMAL(14,2) NOT NULL,
  `tax_amount` DECIMAL(14,2) NOT NULL DEFAULT 0,
  `service_fee` DECIMAL(14,2) NOT NULL DEFAULT 0,
  `discount_amount` DECIMAL(14,2) NOT NULL DEFAULT 0,
  `total_amount` DECIMAL(14,2) NOT NULL,
  `invoice_status` VARCHAR(15) NOT NULL,
  PRIMARY KEY (`invoice_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `invoice_item` (
  `invoice_item_id` BIGINT NOT NULL AUTO_INCREMENT,
  `invoice_id` BIGINT NOT NULL,
  `item_type` VARCHAR(20) NOT NULL,
  `description` VARCHAR(255) NOT NULL,
  `quantity` DECIMAL(10,2) NOT NULL,
  `unit_price` DECIMAL(14,2) NOT NULL,
  `line_total` DECIMAL(14,2) NOT NULL,
  PRIMARY KEY (`invoice_item_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `review` (
  `review_id` BIGINT NOT NULL AUTO_INCREMENT,
  `booking_id` BIGINT NOT NULL,
  `account_id` BIGINT NOT NULL,
  `rating` SMALLINT NOT NULL,
  `review_content` TEXT NOT NULL,
  `review_status` VARCHAR(15) NOT NULL,
  `hidden_reason` VARCHAR(500) NULL,
  `created_at` DATETIME(6) NOT NULL,
  PRIMARY KEY (`review_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `review_image` (
  `review_image_id` BIGINT NOT NULL AUTO_INCREMENT,
  `review_id` BIGINT NOT NULL,
  `image_url` VARCHAR(1000) NOT NULL,
  `display_order` INT NOT NULL DEFAULT 0,
  PRIMARY KEY (`review_image_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `review_reply` (
  `review_reply_id` BIGINT NOT NULL AUTO_INCREMENT,
  `review_id` BIGINT NOT NULL,
  `admin_account_id` BIGINT NOT NULL,
  `reply_content` TEXT NOT NULL,
  `created_at` DATETIME(6) NOT NULL,
  `updated_at` DATETIME(6) NOT NULL,
  PRIMARY KEY (`review_reply_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `notification_outbox` (
  `notification_id` BIGINT NOT NULL AUTO_INCREMENT,
  `account_id` BIGINT NULL,
  `booking_id` BIGINT NULL,
  `recipient_email` VARCHAR(254) NOT NULL,
  `event_type` VARCHAR(40) NOT NULL,
  `subject` VARCHAR(255) NOT NULL,
  `payload` JSON NOT NULL,
  `send_status` VARCHAR(15) NOT NULL,
  `attempt_count` SMALLINT NOT NULL DEFAULT 0,
  `next_retry_at` DATETIME(6) NULL,
  `sent_at` DATETIME(6) NULL,
  `created_at` DATETIME(6) NOT NULL,
  PRIMARY KEY (`notification_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `audit_log` (
  `audit_log_id` BIGINT NOT NULL AUTO_INCREMENT,
  `actor_account_id` BIGINT NULL,
  `action_code` VARCHAR(60) NOT NULL,
  `entity_type` VARCHAR(50) NOT NULL,
  `entity_id` VARCHAR(80) NULL,
  `before_data` JSON NULL,
  `after_data` JSON NULL,
  `reason` VARCHAR(500) NULL,
  `ip_address` VARCHAR(45) NULL,
  `created_at` DATETIME(6) NOT NULL,
  PRIMARY KEY (`audit_log_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `system_setting` (
  `setting_id` BIGINT NOT NULL AUTO_INCREMENT,
  `setting_key` VARCHAR(80) NOT NULL,
  `setting_value` JSON NOT NULL,
  `description` VARCHAR(255) NULL,
  `updated_by` BIGINT NOT NULL,
  `updated_at` DATETIME(6) NOT NULL,
  PRIMARY KEY (`setting_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

ALTER TABLE `account` ADD COLUMN `active_email_key` VARCHAR(254) GENERATED ALWAYS AS (CASE WHEN `deleted_at` IS NULL THEN LOWER(`email`) ELSE NULL END) STORED;
ALTER TABLE `account` ADD UNIQUE KEY `uq_account_active_email` (`active_email_key`);

ALTER TABLE `account` ADD CONSTRAINT `fk_account_role_id` FOREIGN KEY (`role_id`) REFERENCES `role` (`role_id`);

ALTER TABLE `account_session` ADD CONSTRAINT `fk_account_session_account_id` FOREIGN KEY (`account_id`) REFERENCES `account` (`account_id`);

ALTER TABLE `auth_token` ADD CONSTRAINT `fk_auth_token_account_id` FOREIGN KEY (`account_id`) REFERENCES `account` (`account_id`);

ALTER TABLE `hotel_translation` ADD CONSTRAINT `fk_hotel_translation_hotel_id` FOREIGN KEY (`hotel_id`) REFERENCES `hotel` (`hotel_id`) ON DELETE CASCADE;

ALTER TABLE `hotel_image` ADD CONSTRAINT `fk_hotel_image_hotel_id` FOREIGN KEY (`hotel_id`) REFERENCES `hotel` (`hotel_id`) ON DELETE CASCADE;

ALTER TABLE `amenity_translation` ADD CONSTRAINT `fk_amenity_translation_amenity_id` FOREIGN KEY (`amenity_id`) REFERENCES `amenity` (`amenity_id`) ON DELETE CASCADE;

ALTER TABLE `hotel_amenity` ADD CONSTRAINT `fk_hotel_amenity_hotel_id` FOREIGN KEY (`hotel_id`) REFERENCES `hotel` (`hotel_id`) ON DELETE CASCADE;

ALTER TABLE `hotel_amenity` ADD CONSTRAINT `fk_hotel_amenity_amenity_id` FOREIGN KEY (`amenity_id`) REFERENCES `amenity` (`amenity_id`) ON DELETE CASCADE;

ALTER TABLE `hotel_policy` ADD CONSTRAINT `fk_hotel_policy_hotel_id` FOREIGN KEY (`hotel_id`) REFERENCES `hotel` (`hotel_id`);

ALTER TABLE `room_type` ADD CONSTRAINT `fk_room_type_hotel_id` FOREIGN KEY (`hotel_id`) REFERENCES `hotel` (`hotel_id`);

ALTER TABLE `room_type_translation` ADD CONSTRAINT `fk_room_type_translation_room_type_id` FOREIGN KEY (`room_type_id`) REFERENCES `room_type` (`room_type_id`) ON DELETE CASCADE;

ALTER TABLE `room_type_image` ADD CONSTRAINT `fk_room_type_image_room_type_id` FOREIGN KEY (`room_type_id`) REFERENCES `room_type` (`room_type_id`) ON DELETE CASCADE;

ALTER TABLE `room_type_amenity` ADD CONSTRAINT `fk_room_type_amenity_room_type_id` FOREIGN KEY (`room_type_id`) REFERENCES `room_type` (`room_type_id`) ON DELETE CASCADE;

ALTER TABLE `room_type_amenity` ADD CONSTRAINT `fk_room_type_amenity_amenity_id` FOREIGN KEY (`amenity_id`) REFERENCES `amenity` (`amenity_id`) ON DELETE CASCADE;

ALTER TABLE `room` ADD CONSTRAINT `fk_room_room_type_id` FOREIGN KEY (`room_type_id`) REFERENCES `room_type` (`room_type_id`);

ALTER TABLE `room_maintenance` ADD CONSTRAINT `fk_room_maintenance_room_id` FOREIGN KEY (`room_id`) REFERENCES `room` (`room_id`);

ALTER TABLE `room_maintenance` ADD CONSTRAINT `fk_room_maintenance_created_by` FOREIGN KEY (`created_by`) REFERENCES `account` (`account_id`);

ALTER TABLE `room_rate` ADD CONSTRAINT `fk_room_rate_room_type_id` FOREIGN KEY (`room_type_id`) REFERENCES `room_type` (`room_type_id`);

ALTER TABLE `room_rate` ADD CONSTRAINT `fk_room_rate_created_by` FOREIGN KEY (`created_by`) REFERENCES `account` (`account_id`);

ALTER TABLE `room_rate_holiday` ADD CONSTRAINT `fk_room_rate_holiday_room_rate_id` FOREIGN KEY (`room_rate_id`) REFERENCES `room_rate` (`room_rate_id`) ON DELETE CASCADE;

ALTER TABLE `room_rate_holiday` ADD CONSTRAINT `fk_room_rate_holiday_holiday_date_id` FOREIGN KEY (`holiday_date_id`) REFERENCES `holiday_date` (`holiday_date_id`) ON DELETE CASCADE;

ALTER TABLE `deposit_level` ADD CONSTRAINT `fk_deposit_level_updated_by` FOREIGN KEY (`updated_by`) REFERENCES `account` (`account_id`);

ALTER TABLE `promotion` ADD CONSTRAINT `fk_promotion_created_by` FOREIGN KEY (`created_by`) REFERENCES `account` (`account_id`);

ALTER TABLE `promotion_room_type` ADD CONSTRAINT `fk_promotion_room_type_promotion_id` FOREIGN KEY (`promotion_id`) REFERENCES `promotion` (`promotion_id`) ON DELETE CASCADE;

ALTER TABLE `promotion_room_type` ADD CONSTRAINT `fk_promotion_room_type_room_type_id` FOREIGN KEY (`room_type_id`) REFERENCES `room_type` (`room_type_id`) ON DELETE CASCADE;

ALTER TABLE `promotion_redemption` ADD CONSTRAINT `fk_promotion_redemption_promotion_id` FOREIGN KEY (`promotion_id`) REFERENCES `promotion` (`promotion_id`);

ALTER TABLE `promotion_redemption` ADD CONSTRAINT `fk_promotion_redemption_account_id` FOREIGN KEY (`account_id`) REFERENCES `account` (`account_id`);

ALTER TABLE `promotion_redemption` ADD CONSTRAINT `fk_promotion_redemption_booking_id` FOREIGN KEY (`booking_id`) REFERENCES `booking` (`booking_id`);

ALTER TABLE `booking` ADD CONSTRAINT `fk_booking_account_id` FOREIGN KEY (`account_id`) REFERENCES `account` (`account_id`);

ALTER TABLE `booking` ADD CONSTRAINT `fk_booking_created_by` FOREIGN KEY (`created_by`) REFERENCES `account` (`account_id`);

ALTER TABLE `booking_item` ADD CONSTRAINT `fk_booking_item_booking_id` FOREIGN KEY (`booking_id`) REFERENCES `booking` (`booking_id`);

ALTER TABLE `booking_item` ADD CONSTRAINT `fk_booking_item_room_type_id` FOREIGN KEY (`room_type_id`) REFERENCES `room_type` (`room_type_id`);

ALTER TABLE `booking_night_rate` ADD CONSTRAINT `fk_booking_night_rate_booking_item_id` FOREIGN KEY (`booking_item_id`) REFERENCES `booking_item` (`booking_item_id`);

ALTER TABLE `booking_night_rate` ADD CONSTRAINT `fk_booking_night_rate_source_room_rate_id` FOREIGN KEY (`source_room_rate_id`) REFERENCES `room_rate` (`room_rate_id`);

ALTER TABLE `booking_guest` ADD CONSTRAINT `fk_booking_guest_booking_id` FOREIGN KEY (`booking_id`) REFERENCES `booking` (`booking_id`);

ALTER TABLE `booking_guest` ADD CONSTRAINT `fk_booking_guest_assignment_id` FOREIGN KEY (`assignment_id`) REFERENCES `booking_room_assignment` (`assignment_id`);

ALTER TABLE `booking_room_assignment` ADD CONSTRAINT `fk_booking_room_assignment_booking_item_id` FOREIGN KEY (`booking_item_id`) REFERENCES `booking_item` (`booking_item_id`);

ALTER TABLE `booking_room_assignment` ADD CONSTRAINT `fk_booking_room_assignment_room_id` FOREIGN KEY (`room_id`) REFERENCES `room` (`room_id`);

ALTER TABLE `booking_room_assignment` ADD CONSTRAINT `fk_booking_room_assignment_assigned_by` FOREIGN KEY (`assigned_by`) REFERENCES `account` (`account_id`);

ALTER TABLE `booking_status_history` ADD CONSTRAINT `fk_booking_status_history_booking_id` FOREIGN KEY (`booking_id`) REFERENCES `booking` (`booking_id`);

ALTER TABLE `booking_status_history` ADD CONSTRAINT `fk_booking_status_history_changed_by` FOREIGN KEY (`changed_by`) REFERENCES `account` (`account_id`);

ALTER TABLE `payment` ADD CONSTRAINT `fk_payment_booking_id` FOREIGN KEY (`booking_id`) REFERENCES `booking` (`booking_id`);

ALTER TABLE `payment` ADD CONSTRAINT `fk_payment_processed_by` FOREIGN KEY (`processed_by`) REFERENCES `account` (`account_id`);

ALTER TABLE `payment` ADD CONSTRAINT `fk_payment_invoice_id` FOREIGN KEY (`invoice_id`) REFERENCES `invoice` (`invoice_id`);

ALTER TABLE `refund` ADD CONSTRAINT `fk_refund_booking_id` FOREIGN KEY (`booking_id`) REFERENCES `booking` (`booking_id`);

ALTER TABLE `refund` ADD CONSTRAINT `fk_refund_payment_id` FOREIGN KEY (`payment_id`) REFERENCES `payment` (`payment_id`);

ALTER TABLE `refund` ADD CONSTRAINT `fk_refund_processed_by` FOREIGN KEY (`processed_by`) REFERENCES `account` (`account_id`);

ALTER TABLE `invoice` ADD CONSTRAINT `fk_invoice_booking_id` FOREIGN KEY (`booking_id`) REFERENCES `booking` (`booking_id`);

ALTER TABLE `invoice_item` ADD CONSTRAINT `fk_invoice_item_invoice_id` FOREIGN KEY (`invoice_id`) REFERENCES `invoice` (`invoice_id`);

ALTER TABLE `review` ADD CONSTRAINT `fk_review_booking_id` FOREIGN KEY (`booking_id`) REFERENCES `booking` (`booking_id`);

ALTER TABLE `review` ADD CONSTRAINT `fk_review_account_id` FOREIGN KEY (`account_id`) REFERENCES `account` (`account_id`);

ALTER TABLE `review_image` ADD CONSTRAINT `fk_review_image_review_id` FOREIGN KEY (`review_id`) REFERENCES `review` (`review_id`) ON DELETE CASCADE;

ALTER TABLE `review_reply` ADD CONSTRAINT `fk_review_reply_review_id` FOREIGN KEY (`review_id`) REFERENCES `review` (`review_id`);

ALTER TABLE `review_reply` ADD CONSTRAINT `fk_review_reply_admin_account_id` FOREIGN KEY (`admin_account_id`) REFERENCES `account` (`account_id`);

ALTER TABLE `notification_outbox` ADD CONSTRAINT `fk_notification_outbox_account_id` FOREIGN KEY (`account_id`) REFERENCES `account` (`account_id`);

ALTER TABLE `notification_outbox` ADD CONSTRAINT `fk_notification_outbox_booking_id` FOREIGN KEY (`booking_id`) REFERENCES `booking` (`booking_id`);

ALTER TABLE `audit_log` ADD CONSTRAINT `fk_audit_log_actor_account_id` FOREIGN KEY (`actor_account_id`) REFERENCES `account` (`account_id`);

ALTER TABLE `system_setting` ADD CONSTRAINT `fk_system_setting_updated_by` FOREIGN KEY (`updated_by`) REFERENCES `account` (`account_id`);


-- Business unique constraints from RBLB02/RBLB05/RBLB06/RBLB07/RBLB12/RBLB13.
ALTER TABLE `room` ADD UNIQUE KEY `uq_room_number` (`room_number`);
ALTER TABLE `room_type` ADD UNIQUE KEY `uq_room_type_code` (`room_type_code`);
ALTER TABLE `booking` ADD UNIQUE KEY `uq_booking_code` (`booking_code`);
ALTER TABLE `promotion` ADD UNIQUE KEY `uq_promotion_code` (`promo_code`);
ALTER TABLE `payment` ADD UNIQUE KEY `uq_payment_reference` (`payment_reference`);
ALTER TABLE `invoice` ADD UNIQUE KEY `uq_invoice_number` (`invoice_number`);
ALTER TABLE `review` ADD UNIQUE KEY `uq_review_booking` (`booking_id`);
ALTER TABLE `promotion_redemption` ADD UNIQUE KEY `uq_redemption_booking` (`booking_id`);
ALTER TABLE `review_reply` ADD UNIQUE KEY `uq_review_reply_review` (`review_id`);
ALTER TABLE `booking_room_assignment` ADD UNIQUE KEY `uq_assignment_item_room` (`booking_item_id`, `room_id`);
ALTER TABLE `deposit_level` ADD COLUMN `active_percentage_key` DECIMAL(5,2) GENERATED ALWAYS AS (CASE WHEN `is_active` = 1 THEN `percentage` ELSE NULL END) STORED;
ALTER TABLE `deposit_level` ADD UNIQUE KEY `uq_deposit_active_percentage` (`active_percentage_key`);
ALTER TABLE `invoice` ADD COLUMN `valid_booking_id` BIGINT GENERATED ALWAYS AS (CASE WHEN `invoice_status` <> 'VOID' THEN `booking_id` ELSE NULL END) STORED;
ALTER TABLE `invoice` ADD UNIQUE KEY `uq_invoice_valid_booking` (`valid_booking_id`);
ALTER TABLE `room_rate` ADD COLUMN `active_base_room_type_id` BIGINT GENERATED ALWAYS AS (CASE WHEN `is_active` = 1 AND `rate_type` = 'BASE' THEN `room_type_id` ELSE NULL END) STORED;
ALTER TABLE `room_rate` ADD COLUMN `active_weekend_room_type_id` BIGINT GENERATED ALWAYS AS (CASE WHEN `is_active` = 1 AND `rate_type` = 'WEEKEND' THEN `room_type_id` ELSE NULL END) STORED;
ALTER TABLE `room_rate` ADD COLUMN `active_weekend_weekday_no` SMALLINT GENERATED ALWAYS AS (CASE WHEN `is_active` = 1 AND `rate_type` = 'WEEKEND' THEN `weekday_no` ELSE NULL END) STORED;
ALTER TABLE `room_rate` ADD UNIQUE KEY `uq_room_rate_active_base` (`active_base_room_type_id`);
ALTER TABLE `room_rate` ADD UNIQUE KEY `uq_room_rate_active_weekend` (`active_weekend_room_type_id`, `active_weekend_weekday_no`);


-- Domain and tuple-level CHECK constraints (MySQL 8.4 enforces CHECK).
ALTER TABLE `role` ADD CONSTRAINT `ck_role_code` CHECK (`role_code` IN ('CUSTOMER','MANAGER','RECEPTIONIST'));
ALTER TABLE `account` ADD CONSTRAINT `ck_account_status_domain` CHECK (`account_status` IN ('INACTIVE','ACTIVE','LOCKED'));
ALTER TABLE `account` ADD CONSTRAINT `ck_account_failed_login_count` CHECK (`failed_login_count` >= 0);
ALTER TABLE `hotel` ADD CONSTRAINT `ck_hotel_star_rating` CHECK (`star_rating` BETWEEN 1 AND 5);
ALTER TABLE `room_type` ADD CONSTRAINT `ck_room_type_capacity_price` CHECK (`area_sqm` > 0 AND `max_adults` >= 1 AND `max_children` >= 0 AND `base_price` >= 0);
ALTER TABLE `room` ADD CONSTRAINT `ck_room_status_domain` CHECK (`room_status` IN ('VACANT','OCCUPIED','NEEDS_CLEANING','MAINTENANCE'));
ALTER TABLE `room_rate` ADD CONSTRAINT `ck_room_rate_domain` CHECK (`rate_type` IN ('BASE','WEEKEND','SEASON','HOLIDAY') AND `nightly_price` >= 0);
ALTER TABLE `room_rate` ADD CONSTRAINT `ck_room_rate_period_by_type` CHECK ((`rate_type` = 'SEASON' AND `start_date` IS NOT NULL AND `end_date` IS NOT NULL AND `end_date` >= `start_date` AND `weekday_no` IS NULL) OR (`rate_type` = 'WEEKEND' AND `start_date` IS NULL AND `end_date` IS NULL AND `weekday_no` IN (5,6)) OR (`rate_type` = 'BASE' AND `start_date` IS NULL AND `end_date` IS NULL AND `weekday_no` IS NULL) OR (`rate_type` = 'HOLIDAY' AND `start_date` IS NULL AND `end_date` IS NULL AND `weekday_no` IS NULL));
ALTER TABLE `room_maintenance` ADD CONSTRAINT `ck_room_maintenance_period` CHECK (`end_date` >= `start_date`);
ALTER TABLE `auth_token` ADD CONSTRAINT `ck_auth_token_timestamps` CHECK (`expires_at` > `created_at` AND (`used_at` IS NULL OR `used_at` >= `created_at`) AND (`revoked_at` IS NULL OR `revoked_at` >= `created_at`));
ALTER TABLE `booking` ADD CONSTRAINT `ck_booking_status_domain` CHECK (`booking_status` IN ('PENDING_PAYMENT','CONFIRMED','CHECKED_IN','CHECKED_OUT','CANCELLED','PAYMENT_EXPIRED','NO_SHOW'));
ALTER TABLE `booking` ADD CONSTRAINT `ck_booking_payment_status_domain` CHECK (`payment_status` IN ('UNPAID','DEPOSIT_PAID','FULLY_PAID','PAYMENT_FAILED','REFUND_FAILED','PARTIALLY_REFUNDED','REFUNDED'));
ALTER TABLE `booking` ADD CONSTRAINT `ck_booking_source_domain` CHECK (`booking_source` IN ('ONLINE','FRONT_DESK'));
ALTER TABLE `booking` ADD CONSTRAINT `ck_booking_dates_counts` CHECK (`check_out_date` > `check_in_date` AND DATEDIFF(`check_out_date`,`check_in_date`) <= 30 AND `room_count` BETWEEN 1 AND 5 AND `adults` >= `room_count` AND `children` >= 0);
ALTER TABLE `booking` ADD CONSTRAINT `ck_booking_amounts` CHECK (`subtotal_amount` >= 0 AND `discount_amount` >= 0 AND `total_amount` >= 0 AND `deposit_amount` >= 0 AND `paid_amount` >= 0 AND `remaining_amount` >= 0 AND `deposit_percentage` > 0 AND `deposit_percentage` <= 100 AND `currency` = 'VND');
ALTER TABLE `booking_item` ADD CONSTRAINT `ck_booking_item_values` CHECK (`quantity` >= 1 AND `adults` >= `quantity` AND `children` >= 0 AND `line_subtotal` >= 0 AND `line_discount` >= 0 AND `line_total` = `line_subtotal` - `line_discount`);
ALTER TABLE `booking_night_rate` ADD CONSTRAINT `ck_booking_night_rate_values` CHECK (`quantity` >= 1 AND `unit_price` >= 0 AND `night_total` = `unit_price` * `quantity` AND `night_discount` >= 0);
ALTER TABLE `booking_status_history` ADD CONSTRAINT `ck_booking_history_source` CHECK (`changed_source` IN ('USER','ADMIN','SYSTEM_SCHEDULER','PAYMENT_GATEWAY'));
ALTER TABLE `booking_status_history` ADD CONSTRAINT `ck_booking_history_actor` CHECK ((`changed_source` IN ('USER','ADMIN') AND `changed_by` IS NOT NULL) OR (`changed_source` IN ('SYSTEM_SCHEDULER','PAYMENT_GATEWAY') AND `changed_by` IS NULL));
ALTER TABLE `deposit_level` ADD CONSTRAINT `ck_deposit_percentage` CHECK (`percentage` BETWEEN 1 AND 100 AND `percentage` = FLOOR(`percentage`));
ALTER TABLE `promotion` ADD CONSTRAINT `ck_promotion_values` CHECK (`valid_to` > `valid_from` AND `min_nights` >= 1 AND `per_account_limit` >= 1 AND (`max_discount` IS NULL OR `max_discount` >= 0));
ALTER TABLE `promotion` ADD CONSTRAINT `ck_promotion_discount` CHECK ((`discount_type` = 'PERCENT' AND `discount_value` > 0 AND `discount_value` <= 100) OR (`discount_type` = 'FIXED' AND `discount_value` > 0));
ALTER TABLE `payment` ADD CONSTRAINT `ck_payment_amount` CHECK (`amount` > 0);
ALTER TABLE `refund` ADD CONSTRAINT `ck_refund_amount` CHECK (`refund_amount` > 0 AND `cancellation_fee` >= 0);
ALTER TABLE `invoice_item` ADD CONSTRAINT `ck_invoice_item_amounts` CHECK (`quantity` > 0 AND `unit_price` >= 0 AND `line_total` = ROUND(`quantity` * `unit_price`, 2));
ALTER TABLE `review` ADD CONSTRAINT `ck_review_rating_status` CHECK (`rating` BETWEEN 1 AND 5 AND `review_status` IN ('PUBLISHED','HIDDEN') AND CHAR_LENGTH(`review_content`) BETWEEN 10 AND 1000);

CREATE INDEX `ix_booking_status_dates` ON `booking` (`booking_status`,`check_in_date`,`check_out_date`);
CREATE INDEX `ix_booking_hold_expiry` ON `booking` (`booking_status`,`hold_expires_at`);
CREATE INDEX `ix_room_type_hotel_status` ON `room_type` (`hotel_id`,`selling_status`);
CREATE INDEX `ix_room_maintenance_period` ON `room_maintenance` (`room_id`,`start_date`,`end_date`,`maintenance_status`);
CREATE INDEX `ix_notification_retry` ON `notification_outbox` (`send_status`,`next_retry_at`);
CREATE INDEX `ix_audit_entity` ON `audit_log` (`entity_type`,`entity_id`,`created_at`);
SET FOREIGN_KEY_CHECKS=1;
