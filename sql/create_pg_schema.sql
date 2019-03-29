--
-- PostgreSQL database dump
--

-- Dumped from database version 9.5.8
-- Dumped by pg_dump version 9.5.8

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

--
-- Name: feed_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE feed_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: feed; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE feed (
    id integer DEFAULT nextval('feed_id_seq'::regclass) NOT NULL,
    service character varying(16) DEFAULT ''::character varying NOT NULL,
    received timestamp without time zone NOT NULL,
    account_id integer,
    device_id integer,
    device_tag character varying(100),
    headers json,
    body json
);


--
-- Name: file_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE file_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: file; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE file (
    id integer DEFAULT nextval('file_id_seq'::regclass) NOT NULL,
    service character varying(16) DEFAULT ''::character varying NOT NULL,
    received timestamp without time zone NOT NULL,
    account_id integer,
    device_id integer,
    device_tag character varying(100),
    headers json,
    location character varying(250) DEFAULT ''::character varying NOT NULL,
    file_id character varying(4096)
);


--
-- Name: message_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE message_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: message; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE message (
    id integer DEFAULT nextval('message_id_seq'::regclass) NOT NULL,
    service character varying(16) DEFAULT ''::character varying NOT NULL,
    received timestamp without time zone NOT NULL,
    account_id integer,
    device_id integer,
    device_tag character varying(100),
    headers json,
    body json
);


--
-- Name: system_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE system_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: system; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE system (
    id integer DEFAULT nextval('system_id_seq'::regclass) NOT NULL,
    received timestamp without time zone NOT NULL,
    headers json,
    body json,
    message character varying(200) DEFAULT ''::character varying NOT NULL,
    code character varying(200)
);


--
-- Name: feed_id_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY feed
    ADD CONSTRAINT feed_id_pkey PRIMARY KEY (id);


--
-- Name: file_id_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY file
    ADD CONSTRAINT file_id_pkey PRIMARY KEY (id);


--
-- Name: message_id_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY message
    ADD CONSTRAINT message_id_pkey PRIMARY KEY (id);


--
-- Name: system_id_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY system
    ADD CONSTRAINT system_id_pkey PRIMARY KEY (id);


--
-- Name: feed_account_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX feed_account_id ON feed USING btree (account_id);


--
-- Name: feed_device_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX feed_device_id ON feed USING btree (device_id);


--
-- Name: file_account_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX file_account_id ON file USING btree (account_id);


--
-- Name: file_device_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX file_device_id ON file USING btree (device_id);


--
-- Name: message_account_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX message_account_id ON message USING btree (account_id);


--
-- Name: message_device_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX message_device_id ON message USING btree (device_id);


--
-- PostgreSQL database dump complete
--
