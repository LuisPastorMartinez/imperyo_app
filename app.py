ValueError: This app has encountered an error. The original error message is redacted to prevent data leaks. Full error details have been recorded in the logs (if you're on Streamlit Cloud, click on 'Manage app' in the lower right of your app).
Traceback:
File "/mount/src/imperyo_app/app.py", line 226, in <module>
    df_pedidos_temp[col] = df_pedidos_temp[col].apply(
                           ~~~~~~~~~~~~~~~~~~~~~~~~~~^
        lambda x: True if x == 'true' or x == '1' else False
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
File "/home/adminuser/venv/lib/python3.13/site-packages/pandas/core/frame.py", line 10381, in apply
    return op.apply().__finalize__(self, method="apply")
           ~~~~~~~~^^
File "/home/adminuser/venv/lib/python3.13/site-packages/pandas/core/apply.py", line 916, in apply
    return self.apply_standard()
           ~~~~~~~~~~~~~~~~~~~^^
File "/home/adminuser/venv/lib/python3.13/site-packages/pandas/core/apply.py", line 1063, in apply_standard
    results, res_index = self.apply_series_generator()
                         ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
File "/home/adminuser/venv/lib/python3.13/site-packages/pandas/core/apply.py", line 1081, in apply_series_generator
    results[i] = self.func(v, *self.args, **self.kwargs)
                 ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/mount/src/imperyo_app/app.py", line 227, in <lambda>
    lambda x: True if x == 'true' or x == '1' else False
                      ^^^^^^^^^^^
File "/home/adminuser/venv/lib/python3.13/site-packages/pandas/core/generic.py", line 1577, in __nonzero__
    raise ValueError(
    ...<2 lines>...
    )