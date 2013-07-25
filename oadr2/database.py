# A small handler/abstraciton layer for SQLite database connections

import logging
import sqlite3


DEFAULT_DB_PATH = 'oadr2.db'


class DBHandler(object):
    # Member varialbes:
    # --------
    # db_path


    # The following is a list of which functions relate to which class/handler/module.
    # --------
    # EventHandler (event.py):
    #   get_active_events()
    #   update_all_events()
    #   update_event()
    #   get_event()
    #   remove_events()

    
    # Intilize the handler
    #
    # db_path - Path to where the database is located
    def __init__(self, db_path=DEFAULT_DB_PATH):
        self.db_path = db_path
        self.init_database()
        

    # Builds the databse, only if it doesn't already exist
    # with the tables we want in it.
    def init_database(self):
        if self.db_path is None or '':
            raise ValueError( "Database path cannot be empty" )

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        # verify if the table already exists:
        c.execute("pragma table_info('event')")
        if c.fetchone() is not None:
            logging.debug('Database `%s` is setup.', self.db_path)
            return # table exists.
    
        try:
            # NOTE timestamps are SECONDS as a float, not milliseconds.
            # see: http://wiki.python.org/moin/WorkingWithTime
            c.executescript('''
                PRAGMA foreign_keys = ON;
    
                CREATE TABLE event (
                    id INTEGER PRIMARY KEY,
                    vtn_id VARCHAR NOT NULL,
                    event_id VARCHAR NOT NULL,
                    mod_num INT NOT NULL DEFAULT 0,
                    raw_xml TEXT NOT NULL
                );
                CREATE UNIQUE INDEX idx_event_vtn_id ON event (
                    vtn_id, event_id
                );
            ''')
    
            conn.commit()
            logging.debug( "Created tables for database %s", self.db_path)
        except:
            logging.exception( "Error creating tables for database %s", self.db_path)
            conn.rollback()
        finally:
            c.close()
            conn.close()



    ### EventHandler related functions ###

    # Gets the actives events for us from the database
    #
    # Returns: An empty dictionary or a dictionary following the pattern:
    #           dict['event_id'] = '<xml>blob_for_event</xml>'
    def get_active_events(self):
        if self.db_path is None or '':
            raise ValueError( "Database path cannot be empty" )

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        result_dict = {}
    
        try:
            # Do a simple select query
            c.execute('SELECT event_id, raw_xml FROM event')
            rows = c.fetchall()

            # Have the event_id be the key, and the lxml value be the object
            for row in rows:
                result_dict[row[0]] = row[1]
            logging.debug('Retrived active events from the database.')
        except:
            logging.error('Was not able to get the active events.')
        finally:
            c.close()
            conn.close()

        return result_dict
        
        
    # Clears our the current event table and shoves in new ones
    #
    # records - A list of tuples with the folowing format:
    #             ('vtn_id', 'event_id', MOD_NUM(integer), '<xml>for_event</xml>')
    def update_all_events(self, records):
        if self.db_path is None or '':
            raise ValueError( "Database path cannot be empty" )

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
    
        try:
            # Clear out the event table
            c.execute('DELETE FROM event')
            logging.debug('Wiped the event table to update all of the events')

            # Insert them into the database
            c.executemany('Insert INTO event(vtn_id, event_id, mod_num, raw_xml) VALUES(?, ?, ?, ?)', records)
            logging.debug('Inserted the new events into the database')
            conn.commit()
        except:
            logging.error('Was not able to update all of the events in database table.')
            conn.rollback()
        finally:
            c.close()
            conn.close()


    # Updates an existing event, or inserts a new one
    #
    # e_id - EventID of whom we want to insert 
    # mod_num - Current modification number of event  (must be an integer)
    # raw_xml - Raw XML data for event
    # vtn_id - ID of issuing VTN
    def update_event(self, e_id, mod_num, raw_xml, vtn_id):
        if self.db_path is None or '':
            raise ValueError( "Database path cannot be empty" )

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        try:
            # Insert it into the database (or update it)
            c.execute('REPLACE INTO event(vtn_id, event_id, mod_num, raw_xml) VALUES(?, ?, ?, ?)',
                      (vtn_id, e_id, mod_num, raw_xml))
            conn.commit()
            logging.debug('Inserted/updated event_id=`%s` into database.', e_id)
        except:
            logging.error('Was not able to update event [%s] in database table.', e_id)
            conn.rollback()
        finally:
            c.close()
            conn.close()

    
    # Gets an event for us
    #
    # event_id - ID of event
    # Returns: None on failure, or lxml eiEvent object
    def get_event(self, event_id):
        if self.db_path is None or '':
            raise ValueError( "Database path cannot be empty" )

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        raw_xml = None
    
        try:
            # Run the SELECT and see if we got a result
            c.execute('SELECT raw_xml FROM event WHERE event_id=?', (event_id,))
            rows = c.fetchall()

            # Note: there is only one row, w/ one field
            for row in rows:
                raw_xml = row[0]
        except:
            logging.error('Was not able to get event `%s` from database.', event_id)
        finally:
            c.close()
            conn.close()

        return raw_xml 


    # Remove a list of events
    #
    # event_ids - List of event IDs
    def remove_events(self, event_ids):
        if self.db_path is None or '':
            raise ValueError( "Database path cannot be empty" )

        # Exit if we don't have any EventIDs
        if not event_ids:
            return

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Convert them to tuples
        for i in range(len(event_ids)):
            event_ids[i] = (event_ids[i],)
   
        # Delete all of the events
        try:
            c.executemany('DELETE FROM event WHERE event_id=?', event_ids) 
            logging.debug('Removed events from database.')
            conn.commit()
        except:
            logging.error('Was not able to clear out events from the database.')
            conn.rollback()
        finally:
            c.close()
            conn.close()


