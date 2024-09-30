from transitions import Machine
from transitions.extensions.asyncio import AsyncMachine
import asyncio

class Salesman(object):
    
    states = [
        'waiting_start',
        'root',
        'settings',
        'waiting_seller_client_id', 'waiting_seller_token', 'checking_seller_token',
        'waiting_performance_client_id', 'waiting_performance_token', 'checking_performance_token',
    ]
    
    transitions = [
        { 'trigger': 'start', 'source': 'waiting_start', 'dest': 'root' },

        { 'trigger': 'settings', 'source': 'root', 'dest': 'settings' },

        { 'trigger': 'set_seller_token', 'source': 'settings', 'dest': 'waiting_seller_client_id' },
        { 'trigger': 'check_token', 'source': 'waiting_seller_client_id', 'dest': 'waiting_seller_token' },
        { 'trigger': 'check_token', 'source': 'waiting_seller_token', 'dest': 'checking_seller_token' },
        { 'trigger': 'bad_credentials', 'source': 'checking_seller_token', 'dest': 'waiting_seller_client_id'},
        { 'trigger': 'token_checked', 'source': 'checking_seller_token', 'dest': 'settings' },
        
        { 'trigger': 'set_performance_token', 'source': 'settings', 'dest': 'waiting_performance_client_id' },
        { 'trigger': 'check_token', 'source': 'waiting_performance_client_id', 'dest': 'waiting_performance_token' },
        { 'trigger': 'check_token', 'source': 'waiting_performance_token', 'dest': 'checking_performance_token' },
        { 'trigger': 'bad_credentials', 'source': 'checking_performance_token', 'dest': 'waiting_performance_client_id'},
        { 'trigger': 'token_checked', 'source': 'checking_performance_token', 'dest': 'settings' },
    ]
    
    def __init__(self, user):
        self.user = user
        state = self.user.current_state or 'waiting_start'
        self.machine = AsyncMachine(model=self, states=Salesman.states, transitions=Salesman.transitions, initial=state)