def transaction_accouts_hooks():
    arr = {
        'Transaction': {
            'account_id': ['from_account_id', 'to_account_id']
        },
        'SavingClose': {
            'account_id': ['to_account_id'],
            'saving_type_id': ['from_account_id']
        },
        'SavingChange': {
            'saving_type_id': ['from_account_id', 'to_account_id']
        }
    }
    return arr
