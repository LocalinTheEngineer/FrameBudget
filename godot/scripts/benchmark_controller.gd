extends Node3D

const MetricsExporterScript = preload("res://scripts/metrics_exporter.gd")
const CpuNodesScript = preload("res://scripts/workloads/cpu_nodes.gd")
const MeshDrawScript = preload("res://scripts/workloads/mesh_draw.gd")

var workload: String = "idle"
var object_count: int = 100
var seed_value: int = 42
var warmup_s: float = 5.0
var duration_s: float = 15.0
var run_id: String = "manual"
var output_directory: String = ""
var mode: String = "rendered"
var max_fps_value: int = 0
var vsync_value: String = "disabled"
var frame_index: int = 0
var first_tick_us: int = -1
var previous_tick_us: int = -1
var previous_monitor_tick_us: int = -1
var exporter: RefCounted
var nodes: Array[Node3D] = []
var updater: RefCounted

func _ready() -> void:
	_parse_options(OS.get_cmdline_user_args())
	if output_directory.is_empty() or duration_s <= 0 or warmup_s < 0 or object_count < 0 or max_fps_value < 0:
		push_error("Invalid benchmark arguments")
		get_tree().quit(2)
		return
	Engine.max_fps = max_fps_value
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED if vsync_value == "enabled" else DisplayServer.VSYNC_DISABLED)
	exporter = MetricsExporterScript.new()
	if not exporter.start(output_directory, run_id):
		get_tree().quit(3)
		return
	_build_scene()

func _parse_options(args: PackedStringArray) -> void:
	var options: Dictionary = {}
	var index: int = 0
	while index + 1 < args.size():
		options[args[index]] = args[index + 1]
		index += 2
	workload = options.get("--workload", workload)
	object_count = int(options.get("--objects", str(object_count)))
	seed_value = int(options.get("--seed", str(seed_value)))
	warmup_s = float(options.get("--warmup", str(warmup_s)))
	duration_s = float(options.get("--duration", str(duration_s)))
	run_id = options.get("--run-id", run_id)
	output_directory = options.get("--out", output_directory)
	mode = options.get("--mode", mode)
	max_fps_value = int(options.get("--max-fps", str(max_fps_value)))
	vsync_value = options.get("--vsync", vsync_value)

func _build_scene() -> void:
	var base_mesh: BoxMesh = BoxMesh.new()
	base_mesh.size = Vector3(0.4, 0.4, 0.4)
	var material: StandardMaterial3D = StandardMaterial3D.new()
	material.albedo_color = Color(0.4, 0.75, 0.95)
	base_mesh.material = material
	var count: int = 8 if workload == "idle" else object_count
	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	rng.seed = seed_value
	for index in count:
		var node: MeshInstance3D = MeshInstance3D.new()
		node.mesh = base_mesh
		node.position = Vector3(rng.randf_range(-6.0, 6.0), rng.randf_range(-2.0, 2.0), rng.randf_range(-6.0, 6.0))
		add_child(node)
		nodes.append(node)
	if workload == "cpu_nodes":
		updater = CpuNodesScript.new()
	elif workload == "mesh_draw":
		updater = MeshDrawScript.new()
	elif workload != "idle":
		push_error("Unknown workload: " + workload)
		get_tree().quit(2)

func _process(_delta: float) -> void:
	var tick_us: int = Time.get_ticks_usec()
	if first_tick_us < 0:
		first_tick_us = tick_us
		previous_tick_us = tick_us
		return
	var elapsed_s: float = float(tick_us - first_tick_us) / 1000000.0
	var interval_ms: float = float(tick_us - previous_tick_us) / 1000.0
	previous_tick_us = tick_us
	var cpu_ms: float = 0.0
	if updater != null:
		var update_start_us: int = Time.get_ticks_usec()
		updater.update(nodes, frame_index)
		cpu_ms = float(Time.get_ticks_usec() - update_start_us) / 1000.0
	var phase: String = "warmup" if elapsed_s < warmup_s else "measure"
	if interval_ms > 0:
		exporter.sample(frame_index, phase, tick_us, interval_ms, cpu_ms)
		frame_index += 1
	if previous_monitor_tick_us < 0 or tick_us - previous_monitor_tick_us >= 1000000:
		exporter.monitor_sample(tick_us, Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0)
		previous_monitor_tick_us = tick_us
	if elapsed_s >= warmup_s + duration_s:
		var manifest: Dictionary = _manifest()
		if not exporter.finish(manifest):
			get_tree().quit(3)
		else:
			get_tree().quit(0)

func _manifest() -> Dictionary:
	var size: Vector2i = DisplayServer.window_get_size()
	var adapter: String = RenderingServer.get_video_adapter_name()
	if adapter.is_empty():
		adapter = "unknown"
	return {
		"schema_version": 1, "run_id": run_id,
		"utc_time": Time.get_datetime_string_from_system(true) + "Z",
		"tool_version": "0.1.0", "tool_commit": "unknown",
		"engine_version": Engine.get_version_info()["string"], "os": OS.get_name(),
		"renderer": RenderingServer.get_current_rendering_method(),
		"device_info": adapter, "resolution": [size.x, size.y],
		"vsync": vsync_value, "max_fps": Engine.max_fps,
		"seed": seed_value, "workload": workload, "object_count": nodes.size(),
		"warmup_s": warmup_s, "duration_s": duration_s, "mode": mode,
		"camera_path": "fixed", "shadows": false,
		"engine_monitor_period_s": 1.0,
		"engine_monitor_semantics": "Performance.TIME_PROCESS, previous completed process frame, ms",
		"gpu_frame_ms": null,
		"config_hash": "pending_runner_seal"
	}
