CREATE DATABASE device_management;

USE device_management;

CREATE TABLE devices(
    device_id VARCHAR(40) PRIMARY KEY,
    device_name VARCHAR(30) NOT NULL,
    device_type VARCHAR(30) NOT NULL,
    hardware_sn VARCHAR(30) NOT NULL,
    hardware_model VARCHAR(30) NOT NULL,
    software_version VARCHAR(30) NOT NULL,
    software_last_update DATE NOT NULL,
    nic1_type VARCHAR(30),
    nic1_mac VARCHAR(30),
    nic1_ipv4 VARCHAR(30),
    nic2_type VARCHAR(30),
    nic2_mac VARCHAR(30),
    nic2_ipv4 VARCHAR(30),
    dev_description VARCHAR(200) NULL,
    dev_state VARCHAR(30) DEFAULT 'offline' NOT NULL,
    password VARCHAR(60) NOT NULL,
    created_time BIGINT NOT NULL,
    updated_time BIGINT NOT NULL,
    UNIQUE (hardware_sn, hardware_model)
);

CREATE TABLE groups(
    group_id INT AUTO_INCREMENT PRIMARY KEY,
    group_name VARCHAR(30) UNIQUE NOT NULL,
    group_description VARCHAR(200) NULL,
    created_time BIGINT NOT NULL,
    updated_time BIGINT NOT NULL
);

CREATE TABLE relations(
    relation_id INT AUTO_INCREMENT PRIMARY KEY,
    device_id VARCHAR(40) NOT NULL,
    group_id INT NOT NULL,
    UNIQUE (device_id, group_id)
);