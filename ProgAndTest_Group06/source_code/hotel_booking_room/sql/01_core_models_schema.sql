-- Sinh tự động bởi `python -m scripts.generate_sql` – sửa model rồi sinh lại.

CREATE DATABASE IF NOT EXISTS `hotel_booking_system` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE `hotel_booking_system`;

CREATE TABLE holiday_date (
	holiday_date_id BIGINT NOT NULL AUTO_INCREMENT, 
	holiday_date DATE NOT NULL, 
	holiday_name VARCHAR(120) NOT NULL, 
	is_active BOOL NOT NULL DEFAULT true, 
	PRIMARY KEY (holiday_date_id), 
	UNIQUE (holiday_date)
) ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE hotel (
	hotel_id BIGINT NOT NULL AUTO_INCREMENT, 
	star_rating SMALLINT NOT NULL, 
	address VARCHAR(500) NOT NULL, 
	latitude NUMERIC(10, 7), 
	longitude NUMERIC(10, 7), 
	hotline VARCHAR(30) NOT NULL, 
	contact_email VARCHAR(254) NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (hotel_id)
) ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE `role` (
	role_id BIGINT NOT NULL AUTO_INCREMENT, 
	role_code VARCHAR(30) NOT NULL, 
	role_name VARCHAR(100) NOT NULL, 
	description VARCHAR(255), 
	PRIMARY KEY (role_id), 
	UNIQUE (role_code)
) ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE account (
	account_id BIGINT NOT NULL AUTO_INCREMENT, 
	role_id BIGINT NOT NULL, 
	full_name VARCHAR(150) NOT NULL, 
	email VARCHAR(254) NOT NULL, 
	phone VARCHAR(20) NOT NULL, 
	nationality VARCHAR(80), 
	password_hash VARCHAR(255), 
	account_status VARCHAR(20) NOT NULL, 
	failed_login_count SMALLINT NOT NULL, 
	login_locked_until DATETIME, 
	locked_reason VARCHAR(500), 
	locked_until DATETIME, 
	privacy_consent_at DATETIME, 
	deleted_at DATETIME, 
	active_email_key VARCHAR(254) GENERATED ALWAYS AS (CASE WHEN deleted_at IS NULL THEN email ELSE NULL END) STORED, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (account_id), 
	CONSTRAINT ck_account_status CHECK (account_status IN ('INACTIVE','ACTIVE','LOCKED')), 
	FOREIGN KEY(role_id) REFERENCES `role` (role_id)
) ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE UNIQUE INDEX uq_account_email_active ON account (active_email_key);

CREATE TABLE room_type (
	room_type_id BIGINT NOT NULL AUTO_INCREMENT, 
	hotel_id BIGINT NOT NULL, 
	room_type_code VARCHAR(30) NOT NULL, 
	area_sqm NUMERIC(7, 2) NOT NULL, 
	bed_type VARCHAR(30) NOT NULL, 
	max_adults SMALLINT NOT NULL, 
	max_children SMALLINT NOT NULL, 
	view_direction VARCHAR(50), 
	breakfast_included BOOL NOT NULL DEFAULT false, 
	base_price NUMERIC(14, 2) NOT NULL, 
	selling_status VARCHAR(20) NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (room_type_id), 
	CONSTRAINT ck_room_type_selling_status CHECK (selling_status IN ('ON_SALE','DISCONTINUED')), 
	FOREIGN KEY(hotel_id) REFERENCES hotel (hotel_id), 
	UNIQUE (room_type_code)
) ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE booking (
	booking_id BIGINT NOT NULL AUTO_INCREMENT, 
	booking_code VARCHAR(30) NOT NULL, 
	account_id BIGINT, 
	created_by BIGINT, 
	booking_source VARCHAR(15) NOT NULL, 
	check_in_date DATE NOT NULL, 
	check_out_date DATE NOT NULL, 
	adults SMALLINT NOT NULL, 
	children SMALLINT NOT NULL, 
	room_count SMALLINT NOT NULL, 
	guest_contact_name VARCHAR(150) NOT NULL, 
	guest_contact_phone VARCHAR(20) NOT NULL, 
	guest_contact_email VARCHAR(254), 
	special_requests TEXT, 
	estimated_arrival_time TIME, 
	booking_status VARCHAR(25) NOT NULL, 
	payment_status VARCHAR(25) NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	subtotal_amount NUMERIC(14, 2) NOT NULL, 
	discount_amount NUMERIC(14, 2) NOT NULL, 
	total_amount NUMERIC(14, 2) NOT NULL, 
	deposit_percentage NUMERIC(5, 2) NOT NULL, 
	deposit_amount NUMERIC(14, 2) NOT NULL, 
	paid_amount NUMERIC(14, 2) NOT NULL, 
	remaining_amount NUMERIC(14, 2) NOT NULL, 
	hold_expires_at DATETIME, 
	policy_snapshot JSON NOT NULL, 
	terms_accepted_at DATETIME NOT NULL, 
	cancelled_at DATETIME, 
	cancellation_reason VARCHAR(500), 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (booking_id), 
	CONSTRAINT ck_booking_status CHECK (booking_status IN ('PENDING_PAYMENT','CONFIRMED','CHECKED_IN','CHECKED_OUT','CANCELLED','PAYMENT_EXPIRED','NO_SHOW')), 
	CONSTRAINT ck_booking_payment_status CHECK (payment_status IN ('UNPAID','DEPOSIT_PAID','FULLY_PAID','PAYMENT_FAILED','REFUND_FAILED','PARTIALLY_REFUNDED','REFUNDED')), 
	CONSTRAINT ck_booking_source CHECK (booking_source IN ('ONLINE','FRONT_DESK')), 
	CONSTRAINT ck_booking_dates CHECK (check_out_date > check_in_date), 
	CONSTRAINT ck_booking_counts CHECK (room_count >= 1 AND room_count <= 5 AND adults >= room_count AND children >= 0), 
	CONSTRAINT ck_booking_amounts CHECK (subtotal_amount >= 0 AND discount_amount >= 0 AND total_amount >= 0 AND deposit_amount >= 0 AND paid_amount >= 0 AND remaining_amount >= 0), 
	CONSTRAINT ck_booking_deposit_pct CHECK (deposit_percentage > 0 AND deposit_percentage <= 100), 
	UNIQUE (booking_code), 
	FOREIGN KEY(account_id) REFERENCES account (account_id), 
	FOREIGN KEY(created_by) REFERENCES account (account_id)
) ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE INDEX ix_booking_account_status ON booking (account_id, booking_status);
CREATE INDEX ix_booking_status_dates ON booking (booking_status, check_in_date, check_out_date);
CREATE INDEX ix_booking_status_hold ON booking (booking_status, hold_expires_at);

CREATE TABLE deposit_level (
	deposit_level_id BIGINT NOT NULL AUTO_INCREMENT, 
	percentage NUMERIC(5, 2) NOT NULL, 
	is_active BOOL NOT NULL DEFAULT true, 
	effective_from DATETIME NOT NULL, 
	effective_to DATETIME, 
	updated_by BIGINT NOT NULL, 
	active_percentage_key NUMERIC(5, 2) GENERATED ALWAYS AS (CASE WHEN is_active = 1 THEN percentage ELSE NULL END) STORED, 
	PRIMARY KEY (deposit_level_id), 
	CONSTRAINT ck_deposit_pct CHECK (percentage >= 1 AND percentage <= 100), 
	FOREIGN KEY(updated_by) REFERENCES account (account_id)
) ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE UNIQUE INDEX uq_deposit_active_pct ON deposit_level (active_percentage_key);

CREATE TABLE promotion (
	promotion_id BIGINT NOT NULL AUTO_INCREMENT, 
	promo_code VARCHAR(40) NOT NULL, 
	discount_type VARCHAR(10) NOT NULL, 
	discount_value NUMERIC(14, 2) NOT NULL, 
	max_discount NUMERIC(14, 2), 
	min_nights SMALLINT NOT NULL, 
	min_order_value NUMERIC(14, 2) NOT NULL, 
	valid_from DATETIME NOT NULL, 
	valid_to DATETIME NOT NULL, 
	total_usage_limit INTEGER, 
	per_account_limit INTEGER NOT NULL, 
	used_count INTEGER NOT NULL, 
	promotion_status VARCHAR(15) NOT NULL, 
	is_public BOOL NOT NULL DEFAULT false, 
	created_by BIGINT NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (promotion_id), 
	CONSTRAINT ck_promo_type CHECK (discount_type IN ('PERCENT','FIXED')), 
	CONSTRAINT ck_promo_status CHECK (promotion_status IN ('ACTIVE','PAUSED','EXPIRED')), 
	CONSTRAINT ck_promo_validity CHECK (valid_to > valid_from), 
	CONSTRAINT ck_promo_limits CHECK (min_nights >= 1 AND per_account_limit >= 1), 
	UNIQUE (promo_code), 
	FOREIGN KEY(created_by) REFERENCES account (account_id)
) ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE room (
	room_id BIGINT NOT NULL AUTO_INCREMENT, 
	room_type_id BIGINT NOT NULL, 
	room_number VARCHAR(20) NOT NULL, 
	floor_number SMALLINT NOT NULL, 
	room_status VARCHAR(20) NOT NULL, 
	is_active BOOL NOT NULL DEFAULT true, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (room_id), 
	CONSTRAINT ck_room_status CHECK (room_status IN ('VACANT','OCCUPIED','NEEDS_CLEANING','MAINTENANCE')), 
	FOREIGN KEY(room_type_id) REFERENCES room_type (room_type_id), 
	UNIQUE (room_number)
) ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE room_rate (
	room_rate_id BIGINT NOT NULL AUTO_INCREMENT, 
	room_type_id BIGINT NOT NULL, 
	rate_type VARCHAR(20) NOT NULL, 
	start_date DATE, 
	end_date DATE, 
	weekday_no SMALLINT, 
	nightly_price NUMERIC(14, 2) NOT NULL, 
	is_active BOOL NOT NULL DEFAULT true, 
	created_by BIGINT NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (room_rate_id), 
	CONSTRAINT ck_rate_type CHECK (rate_type IN ('BASE','WEEKEND','SEASON','HOLIDAY')), 
	CONSTRAINT ck_rate_price CHECK (nightly_price >= 0), 
	FOREIGN KEY(room_type_id) REFERENCES room_type (room_type_id), 
	FOREIGN KEY(created_by) REFERENCES account (account_id)
) ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE INDEX ix_room_rate_room_type_id ON room_rate (room_type_id);

CREATE TABLE system_setting (
	setting_id BIGINT NOT NULL AUTO_INCREMENT, 
	setting_key VARCHAR(80) NOT NULL, 
	setting_value JSON NOT NULL, 
	description VARCHAR(255), 
	updated_by BIGINT NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (setting_id), 
	UNIQUE (setting_key), 
	FOREIGN KEY(updated_by) REFERENCES account (account_id)
) ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE booking_item (
	booking_item_id BIGINT NOT NULL AUTO_INCREMENT, 
	booking_id BIGINT NOT NULL, 
	room_type_id BIGINT NOT NULL, 
	quantity SMALLINT NOT NULL, 
	adults SMALLINT NOT NULL, 
	children SMALLINT NOT NULL, 
	line_subtotal NUMERIC(14, 2) NOT NULL, 
	line_discount NUMERIC(14, 2) NOT NULL, 
	line_total NUMERIC(14, 2) NOT NULL, 
	PRIMARY KEY (booking_item_id), 
	CONSTRAINT uq_booking_item_type UNIQUE (booking_id, room_type_id), 
	CONSTRAINT ck_item_counts CHECK (quantity >= 1 AND adults >= quantity AND children >= 0), 
	FOREIGN KEY(booking_id) REFERENCES booking (booking_id), 
	FOREIGN KEY(room_type_id) REFERENCES room_type (room_type_id)
) ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE INDEX ix_item_roomtype_booking ON booking_item (room_type_id, booking_id);

CREATE TABLE booking_status_history (
	booking_status_history_id BIGINT NOT NULL AUTO_INCREMENT, 
	booking_id BIGINT NOT NULL, 
	old_status VARCHAR(25), 
	new_status VARCHAR(25) NOT NULL, 
	changed_by BIGINT, 
	changed_source VARCHAR(20) NOT NULL, 
	change_reason VARCHAR(500), 
	changed_at DATETIME NOT NULL, 
	PRIMARY KEY (booking_status_history_id), 
	CONSTRAINT ck_history_source CHECK (changed_source IN ('USER','ADMIN','SYSTEM_SCHEDULER','PAYMENT_GATEWAY')), 
	CONSTRAINT ck_history_actor CHECK ((changed_source IN ('USER','ADMIN') AND changed_by IS NOT NULL) OR (changed_source IN ('SYSTEM_SCHEDULER','PAYMENT_GATEWAY') AND changed_by IS NULL)), 
	FOREIGN KEY(booking_id) REFERENCES booking (booking_id), 
	FOREIGN KEY(changed_by) REFERENCES account (account_id)
) ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE INDEX ix_booking_status_history_booking_id ON booking_status_history (booking_id);

CREATE TABLE promotion_redemption (
	redemption_id BIGINT NOT NULL AUTO_INCREMENT, 
	promotion_id BIGINT NOT NULL, 
	account_id BIGINT NOT NULL, 
	booking_id BIGINT NOT NULL, 
	discount_amount NUMERIC(14, 2) NOT NULL, 
	redeemed_at DATETIME NOT NULL, 
	redemption_status VARCHAR(15) NOT NULL, 
	PRIMARY KEY (redemption_id), 
	CONSTRAINT ck_redeem_status CHECK (redemption_status IN ('RESERVED','CONSUMED','RELEASED')), 
	FOREIGN KEY(promotion_id) REFERENCES promotion (promotion_id), 
	FOREIGN KEY(account_id) REFERENCES account (account_id), 
	UNIQUE (booking_id), 
	FOREIGN KEY(booking_id) REFERENCES booking (booking_id)
) ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE INDEX ix_promotion_redemption_promotion_id ON promotion_redemption (promotion_id);

CREATE TABLE promotion_room_type (
	promotion_id BIGINT NOT NULL, 
	room_type_id BIGINT NOT NULL, 
	PRIMARY KEY (promotion_id, room_type_id), 
	FOREIGN KEY(promotion_id) REFERENCES promotion (promotion_id), 
	FOREIGN KEY(room_type_id) REFERENCES room_type (room_type_id)
) ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE room_maintenance (
	maintenance_id BIGINT NOT NULL AUTO_INCREMENT, 
	room_id BIGINT NOT NULL, 
	start_date DATE NOT NULL, 
	end_date DATE NOT NULL, 
	reason VARCHAR(500) NOT NULL, 
	maintenance_status VARCHAR(20) NOT NULL, 
	created_by BIGINT NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (maintenance_id), 
	CONSTRAINT ck_maint_dates CHECK (end_date >= start_date), 
	CONSTRAINT ck_maint_status CHECK (maintenance_status IN ('PLANNED','IN_PROGRESS','COMPLETED','CANCELLED')), 
	FOREIGN KEY(room_id) REFERENCES room (room_id), 
	FOREIGN KEY(created_by) REFERENCES account (account_id)
) ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE INDEX ix_maint_room_dates ON room_maintenance (room_id, start_date, end_date);

CREATE TABLE room_rate_holiday (
	room_rate_id BIGINT NOT NULL, 
	holiday_date_id BIGINT NOT NULL, 
	PRIMARY KEY (room_rate_id, holiday_date_id), 
	FOREIGN KEY(room_rate_id) REFERENCES room_rate (room_rate_id), 
	FOREIGN KEY(holiday_date_id) REFERENCES holiday_date (holiday_date_id)
) ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE booking_night_rate (
	booking_night_rate_id BIGINT NOT NULL AUTO_INCREMENT, 
	booking_item_id BIGINT NOT NULL, 
	stay_date DATE NOT NULL, 
	rate_type_applied VARCHAR(20) NOT NULL, 
	source_room_rate_id BIGINT, 
	unit_price NUMERIC(14, 2) NOT NULL, 
	quantity SMALLINT NOT NULL, 
	night_total NUMERIC(14, 2) NOT NULL, 
	night_discount NUMERIC(14, 2) NOT NULL, 
	PRIMARY KEY (booking_night_rate_id), 
	CONSTRAINT uq_night_rate UNIQUE (booking_item_id, stay_date), 
	CONSTRAINT ck_night_rate_type CHECK (rate_type_applied IN ('BASE','WEEKEND','SEASON','HOLIDAY')), 
	FOREIGN KEY(booking_item_id) REFERENCES booking_item (booking_item_id), 
	FOREIGN KEY(source_room_rate_id) REFERENCES room_rate (room_rate_id)
) ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE booking_room_assignment (
	assignment_id BIGINT NOT NULL AUTO_INCREMENT, 
	booking_item_id BIGINT NOT NULL, 
	room_id BIGINT NOT NULL, 
	assigned_at DATETIME NOT NULL, 
	released_at DATETIME, 
	assigned_by BIGINT NOT NULL, 
	is_upgrade BOOL NOT NULL DEFAULT false, 
	upgrade_reason VARCHAR(500), 
	PRIMARY KEY (assignment_id), 
	CONSTRAINT uq_assignment_item_room UNIQUE (booking_item_id, room_id), 
	FOREIGN KEY(booking_item_id) REFERENCES booking_item (booking_item_id), 
	FOREIGN KEY(room_id) REFERENCES room (room_id), 
	FOREIGN KEY(assigned_by) REFERENCES account (account_id)
) ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE booking_guest (
	booking_guest_id BIGINT NOT NULL AUTO_INCREMENT, 
	booking_id BIGINT NOT NULL, 
	assignment_id BIGINT, 
	full_name VARCHAR(150) NOT NULL, 
	phone VARCHAR(20), 
	nationality VARCHAR(80), 
	document_type VARCHAR(20), 
	document_number_encrypted BLOB(512), 
	document_key_version VARCHAR(30), 
	is_primary_guest BOOL NOT NULL DEFAULT false, 
	PRIMARY KEY (booking_guest_id), 
	FOREIGN KEY(booking_id) REFERENCES booking (booking_id), 
	FOREIGN KEY(assignment_id) REFERENCES booking_room_assignment (assignment_id)
) ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;
