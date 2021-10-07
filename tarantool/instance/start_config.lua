box.cfg {
	listen = 'localhost:3301';
	background = true;
	log = '/var/log/tarantool/cur.log';
	pid_file = '/var/run/tarantool/start_config.pid';

	io_collect_interval = nil;
	readahead = 16320;

	memtx_memory = 128 * 1024 * 1024 * 20; -- 128Mb
	memtx_min_tuple_size = 16;
	memtx_max_tuple_size = 128 * 1024 * 1024; -- 128Mb

	vinyl_memory = 128 * 1024 * 1024 * 50; -- 128Mb
	vinyl_cache = 128 * 1024 * 1024; -- 128Mb
	vinyl_max_tuple_size = 128 * 1024 * 1024; -- 128Mb
	vinyl_write_threads = 2;

	wal_max_size = 256 * 1024 * 1024;
	checkpoint_interval = 60 * 60; -- one hour
	checkpoint_count = 6;

	log_level = 5;
}



box.once("bootstrap", function()

	file_binary = box.schema.create_space('file_binary')
	file_binary:format({
	{name='id', type='unsigned'},
	{name='date', type='integer'},
	{name='description', type='string'},
	{name='data', type='string'}
	})
	box.schema.sequence.create('file_binary_seq',{min=1, start=1,cycle=true})
	file_binary:create_index('primary', {unique=true, type='tree', parts={'id'}, sequence='file_binary_seq'})

	message_log = box.schema.create_space('message_log', {engine='vinyl'})
	message_log:format({
	{name='id', type='unsigned'},
	{name='organisation_id', type='integer'},
	{name='from_a', type='string'},
	{name='to_a', type='string'},
	{name='remote_ip', type='string'},
	{name='subject', type='string'},
	{name='status', type='string'},
	{name='date', type='integer'},
	{name='log', type='string'}
	})
	box.schema.sequence.create('message_log_seq',{min=1, start=1,cycle=true})
	message_log:create_index('id', {unique=true, type='tree', parts={'id'}, sequence='message_log_seq'})
	message_log:create_index('organisation_id', {unique=false, type='tree', parts={'organisation_id'}})
	message_log:create_index('from_a', {unique=false, type='tree', parts={'from_a'}})
	message_log:create_index('to_a', {unique=false, type='tree', parts={'to_a'}})
	message_log:create_index('remote_ip', {unique=false, type='tree', parts={'remote_ip'}})
	message_log:create_index('subject', {unique=false, type='tree', parts={'subject'}})
	message_log:create_index('status', {unique=false, type='tree', parts={'status'}})

	filter_list = box.schema.create_space('filter_list')
	filter_list:format({
	{name='id', type='unsigned'},
	{name='organisation_id', type='integer'},
	{name='value', type='string'},
	{name='action', type='string'},
	{name='date', type='integer'},
	{name='description', type='string'}
	})
	box.schema.sequence.create('filter_list_seq',{min=1, start=1,cycle=true})
	filter_list:create_index('id', {unique=true, type='tree', parts={'id'}, sequence='filter_list_seq'})
	filter_list:create_index('secondary', {unique=false, parts = {
	{field = 2, type = 'integer'},
	{field = 3, type = 'string'}
	}})

	global_filter_list = box.schema.create_space('global_filter_list')
	global_filter_list:format({
	{name='value', type='string'},
	{name='action', type='string'},
	{name='date', type='integer'},
	{name='description', type='string'}
	})
	global_filter_list:create_index('primary', {unique=true, type='tree', parts={'value'}})

	greylite = box.schema.create_space('greylite')
	greylite:format({
	{name='value', type='string'},
	{name='count', type='integer'},
	{name='date', type='integer'}
	})
	greylite:create_index('primary', {unique=true, type='tree', parts={'value'}})

	queue_message = box.schema.create_space('queue_message', {engine='vinyl'})
	queue_message:format({
	{name='id', type='unsigned'},
	{name='organisation_id', type='integer'},
	{name='id_in_db', type='integer'},
	{name='create_date', type='integer'},
	{name='send_date', type='integer'},
	{name='log', type='string'}
	})
	box.schema.sequence.create('queue_message_seq',{min=1, start=1,cycle=true})
	queue_message:create_index('id', {unique=true, type='tree', parts={'id'}, sequence='queue_message_seq'})
	queue_message:create_index('organisation_id', {unique=false, type='tree', parts={'organisation_id'}})
	queue_message:create_index('id_in_db', {unique=false, type='tree', parts={'id_in_db'}})

	space_cleaner_code = [[
	function(time, colum, space)
		local s, e, result, tr_return, i
		result = {}
		i = 1
		for s,e in box.space[space]:pairs() do
			if e[colum] < time then
				box.space[space]:delete(e[1])
				result[i] = e[1]
				i = i + 1
			end
		end
		return result
	end
	]]
	box.schema.func.create('space_cleaner', {body = space_cleaner_code, })

	queue_push_code = [[
	function(time, colum, space)
		local s, e, result, tr_return, i
		result = {}
		i = 1
		for s,e in box.space[space]:pairs() do
			if e[colum] < time then
				tr_return = {}
				tr_return[1] = e[1]
				tr_return[2] = e[6]
				result[i] = tr_return
				i = i + 1
			end
		end
		return result
	end
	]]
	box.schema.func.create('queue_push', {body = queue_push_code})


end)

box.schema.user.passwd('admin', 'yFtLch8hUe')
