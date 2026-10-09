extends RefCounted

func update(nodes: Array[Node3D], frame_index: int) -> void:
	var phase: float = float(frame_index) * 0.01
	for index in nodes.size():
		var node: Node3D = nodes[index]
		var value: float = phase + float(index) * 0.05
		node.position.y = sin(value) * 0.5
		node.rotation.y = cos(value) * 0.25
