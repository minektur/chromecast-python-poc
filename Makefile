PROTOC = /usr/local/bin/protoc


cast_channel_pb2.py: cast_channel.proto
	$(PROTOC) --python_out=. cast_channel.proto
