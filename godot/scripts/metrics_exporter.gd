extends RefCounted
class_name MetricsExporter

var output_directory: String
var run_id: String
var stream: FileAccess
var monitor_stream: FileAccess

func start(directory: String, identifier: String) -> bool:
	output_directory = directory
	run_id = identifier
	var error: Error = DirAccess.make_dir_recursive_absolute(directory)
	if error != OK:
		push_error("Cannot create output directory: " + error_string(error))
		return false
	stream = FileAccess.open(directory.path_join("samples.csv"), FileAccess.WRITE)
	if stream == null:
		push_error("Cannot open samples.csv: " + error_string(FileAccess.get_open_error()))
		return false
	stream.store_line("schema_version,run_id,frame_index,phase,time_us,frame_interval_ms,workload_cpu_ms")
	monitor_stream = FileAccess.open(directory.path_join("engine_monitor.jsonl"), FileAccess.WRITE)
	if monitor_stream == null:
		push_error("Cannot open engine_monitor.jsonl")
		stream.close()
		return false
	return true

func sample(index: int, phase: String, time_us: int, interval_ms: float, cpu_ms: float) -> void:
	stream.store_csv_line(PackedStringArray([
		"1", run_id, str(index), phase, str(time_us), str(interval_ms), str(cpu_ms)
	]))

func monitor_sample(time_us: int, process_ms: float) -> void:
	monitor_stream.store_line(JSON.stringify({"time_us": time_us, "engine_process_ms": process_ms}))

func finish(manifest: Dictionary) -> bool:
	stream.flush()
	stream.close()
	monitor_stream.flush()
	monitor_stream.close()
	var file: FileAccess = FileAccess.open(output_directory.path_join("manifest.json"), FileAccess.WRITE)
	if file == null:
		push_error("Cannot open manifest.json: " + error_string(FileAccess.get_open_error()))
		return false
	file.store_string(JSON.stringify(manifest, "  ", true) + "\n")
	file.close()
	return true
