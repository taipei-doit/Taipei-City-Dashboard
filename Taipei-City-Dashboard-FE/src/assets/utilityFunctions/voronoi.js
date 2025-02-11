// Node for the binary search tree
class BSTNode {
	constructor(val) {
		this.val = val;
		this.left = null;
		this.right = null;
	}
}

// A binary search tree is implemented to store and find all edges efficiently (hopefully)
// Implementation reference: https://arsenekuo.com/post/2021/12/13/implementation-of-bst-in-javascript
class BinarySearchTree {
	constructor() {
		this.root = null;
	}

	insert(val) {
		const newNode = new BSTNode(val);
		if (!this.root) {
			this.root = newNode;
			return this;
		}
		let currentNode = this.root;
		while (currentNode) {
			if (compareEdges(val, currentNode.val) === 1) return undefined;
			if (compareEdges(val, currentNode.val) === 0) {
				if (!currentNode.right) {
					currentNode.right = newNode;
					return this;
				}
				currentNode = currentNode.right;
			} else {
				// compareEdges(val, currentNode.val) === 2
				if (!currentNode.left) {
					currentNode.left = newNode;
					return this;
				}
				currentNode = currentNode.left;
			}
		}
	}

	find(val) {
		if (!this.root) return false;
		let currentNode = this.root;
		while (currentNode) {
			if (compareEdges(val, currentNode.val) === 2) {
				currentNode = currentNode.left;
			} else if (compareEdges(val, currentNode.val) === 0) {
				currentNode = currentNode.right;
			} else {
				return currentNode;
			}
		}
		return false;
	}

	remove(val) {
		if (val === null || val === undefined) return undefined;
		this.root = this.removeHelper(val, this.root);
	}

	removeHelper(val, currentNode) {
		if (!currentNode) return undefined;
		if (compareEdges(val, currentNode.val) === 2) {
			currentNode.left = this.removeHelper(val, currentNode.left);
			return currentNode;
		} else if (compareEdges(val, currentNode.val) === 0) {
			currentNode.right = this.removeHelper(val, currentNode.right);
			return currentNode;
		}
		if (!currentNode.left && !currentNode.right) {
			return null;
		} else if (!currentNode.left) {
			return currentNode.right;
		} else if (!currentNode.right) {
			return currentNode.left;
		} else {
			let minRightChildNode = this.findMinValue(currentNode.right);
			currentNode.val = minRightChildNode.val;
			currentNode.right = this.removeHelper(
				minRightChildNode.val,
				currentNode.right
			);
			return currentNode;
		}
	}

	findMinValue(node) {
		if (node.left) {
			return this.findMinValue(node.left);
		}
		return node;
	}
}

// EdgeManager uses a binary search tree to manage all edges
class EdgeManager {
	constructor() {
		this.tree = new BinarySearchTree();
	}

	// When a triangle is initialized, it calls this function to check whether its edges are already in the BST.
	// If so, make a new reference from the edge to the triangle.
	// If not, insert the new edge and make a reference from the edge to the triangle.
	assignEdge(p1, p2, triangle) {
		let newEdge = new Edge(p1, p2);
		let node = this.tree.find(newEdge);

		if (node === false) {
			// the edge is not yet in the BST
			newEdge.t1 = triangle;
			newEdge.p1.lastEdgeConnected = newEdge;
			newEdge.p2.lastEdgeConnected = newEdge;
			this.tree.insert(newEdge);
			return newEdge;
		} else {
			// the edge is already in the BST
			if (node.val.t1 === null) {
				node.val.t1 = triangle;
			} else if (node.val.t2 === null) {
				node.val.t2 = triangle;
			}
			// else {
			// 	console.log("Both t1 and t2 are already assigned? Probably a bug.");
			// }
			return node.val;
		}
	}

	// When a triangle is removed from the triangulation,
	// edge manager finds its three edges and remove their reference to it.
	removeTriangle(triangle) {
		for (let i = 0; i < 3; i++) {
			let node = this.tree.find(triangle.edges[i]);
			if (node !== false) {
				if (node.val.t1 === triangle) {
					node.val.t1 = null;
				}
				if (node.val.t2 === triangle) {
					node.val.t2 = null;
				}
			}
		}
	}
}

let edgeManager = new EdgeManager();

class Triangle {
	constructor(p1, p2, p3) {
		this.points = [p1, p2, p3];
		this.edges = [
			edgeManager.assignEdge(p1, p2, this),
			edgeManager.assignEdge(p2, p3, this),
			edgeManager.assignEdge(p3, p1, this),
		];
		this.center = findCenter(p1, p2, p3); // center of the circumcircle
		this.radius2 = this.center.distance2(p1); // radius of the circumcircle
	}

	// Check whether a point is in the triangle's circumcircle
	circumcircleContains(p) {
		return this.center.distance2(p) < this.radius2;
	}
}

class Edge {
	constructor(pa, pb) {
		// p1 always has smaller ID
		if (pa.id <= pb.id) {
			this.p1 = pa;
			this.p2 = pb;
		} else {
			this.p1 = pb;
			this.p2 = pa;
		}

		// Reference to two neighboring triangles
		this.t1 = null;
		this.t2 = null;
	}
}

let pointID = 0;

class Point {
	constructor(x, y) {
		// Each point has a unique ID for comparison
		this.id = pointID;

		this.x = x;
		this.y = y;

		// Reference to the last edge connected to this point
		this.lastEdgeConnected = null;

		pointID += 1;
	}

	equals(p) {
		return this.id === p.id;
	}

	distance2(p) {
		return (this.x - p.x) ** 2 + (this.y - p.y) ** 2;
	}

	toArray() {
		return [this.x, this.y];
	}
}

// Input: p1, p2, p3: three points from a triangle
// Output: A new point at the circumcenter of the triangle
function findCenter(p1, p2, p3) {
	let d = p1.x * (p2.y - p3.y) + p2.x * (p3.y - p1.y) + p3.x * (p1.y - p2.y);

	// Note: When two points have the same coordinates, d === 0.
	//       This case has been avoided with AddVoronoiMapLayer() in mapStore.js.

	let x =
		(p1.x ** 2 + p1.y ** 2) * (p2.y - p3.y) +
		(p2.x ** 2 + p2.y ** 2) * (p3.y - p1.y) +
		(p3.x ** 2 + p3.y ** 2) * (p1.y - p2.y);
	let y =
		(p1.x ** 2 + p1.y ** 2) * (p3.x - p2.x) +
		(p2.x ** 2 + p2.y ** 2) * (p1.x - p3.x) +
		(p3.x ** 2 + p3.y ** 2) * (p2.x - p1.x);

	let p = new Point(x / d / 2, y / d / 2);
	return p;
}

// This function defines an order for the edges, which is used to determine the position of an edge in the BST.
// Output:
// 0: e1 > e2
// 1: e1 = e2
// 2: e1 < e2
function compareEdges(e1, e2) {
	// Compare p1 (the point with smaller ID) first.
	if (e1.p1.id > e2.p1.id) {
		return 0;
	}
	if (e1.p1.id < e2.p1.id) {
		return 2;
	}
	// Then compare p2.
	if (e1.p2.id > e2.p2.id) {
		return 0;
	}
	if (e1.p2.id < e2.p2.id) {
		return 2;
	}
	return 1;
}

// Input: An array of Point
// Effect:
// - determine lastEdgeConnected of each point
// - determine the relationship between edges and triangles
function BowyerWatson(points) {
	// Make two huge triangles that cover all of Taipei
	let cornerPoints = [
		new Point(121.1, 25.272604303072),
		new Point(122, 25.272604303072),
		new Point(122, 24.939016012761282),
		new Point(121.1, 24.939016012761282),
	];
	let superTriangle1 = new Triangle(
		cornerPoints[0],
		cornerPoints[1],
		cornerPoints[2]
	);
	let superTriangle2 = new Triangle(
		cornerPoints[0],
		cornerPoints[3],
		cornerPoints[2]
	);

	let triangulation = [superTriangle1, superTriangle2];

	points.forEach((p) => {
		let affectedEdges = [];

		// Remove all triangles whose circumcircle overlaps with the point, and collect all affected edges.
		triangulation = triangulation.filter((t) => {
			if (t.circumcircleContains(p)) {
				edgeManager.removeTriangle(t);
				affectedEdges = affectedEdges.concat(t.edges);
				return false;
			}
			return true;
		});

		// Find all unique edges in the affected edges
		let uniqueEdges = [];

		for (var i = 0; i < affectedEdges.length; ++i) {
			var isUnique = true;

			// See if edge is unique
			for (var j = 0; j < affectedEdges.length; ++j) {
				if (i != j && affectedEdges[i] === affectedEdges[j]) {
					isUnique = false;
					edgeManager.tree.remove(affectedEdges[i]);
					break;
				}
			}

			if (isUnique) {
				uniqueEdges.push(affectedEdges[i]);
			}
		}

		// Form new triangles by connecting each unique edge to the point
		uniqueEdges.forEach((e) => {
			triangulation.push(new Triangle(e.p1, e.p2, p));
		});
	});
}

// Input: A Point
// Output: A 2D array representing the Voronoi cell that contains the point
// [[x1, y1], [x2, y2]...]
function findVoronoiCell(point) {
	// Assume PQ is the lastEdgeConnected of P, the algorithm goes from triangle 0 to 5
	// and push each of their circumcenter coordinates into cellPath.
	//
	//    Q -------
	//   / \  1  / \
	//  /   \   /   \
	// /  0  \ /  2  \
	// ------ P ------
	// \  5  / \  3  /
	//  \   /   \   /
	//   \ /  4  \ /
	//    ---------

	let currentEdge = point.lastEdgeConnected;
	if (
		currentEdge === null ||
		currentEdge.t1 === null ||
		currentEdge.t2 === null
	) {
		return null;
	}

	let firstPoint = currentEdge.t1.center;
	let cellPath = [
		currentEdge.t1.center.toArray(),
		currentEdge.t2.center.toArray(),
	];
	let currentTriangle = currentEdge.t2;

	// Go through (1) each edge connected to the point and (2) each triangle surrounding the point.
	while (currentTriangle.center !== firstPoint) {
		let i = 0;
		for (i = 0; i < 3; i++) {
			if (
				currentEdge !== currentTriangle.edges[i] &&
				(currentTriangle.edges[i].p1 === point ||
					currentTriangle.edges[i].p2 === point)
			) {
				currentEdge = currentTriangle.edges[i];
				currentTriangle =
					currentEdge.t1 === currentTriangle
						? currentEdge.t2
						: currentEdge.t1;
				break;
			}
		}

		if (i === 3) {
			return null;
		}

		cellPath.push(currentTriangle.center.toArray());
	}

	return cellPath;
}

// Voronoi algorithm: An algorithm that generates Voronoi diagram from a set of points.
//
// It first finds the Delaunay triangulation for the input points, and then connects
// every circumcenter in the triangulation to obtain the Voronoi diagram.
//
// Please refer to the following links for details:
// https://www.baeldung.com/cs/voronoi-diagram
// https://www.gorillasun.de/blog/bowyer-watson-algorithm-for-delaunay-triangulation/
//
// Note: In theory, the complexity of this algorithm is O(n^2), which can be improved upon,
//       by either good optimization or switching to Fortune's algorithm (https://en.wikipedia.org/wiki/Fortune%27s_algorithm)
//
// Input:
// - data: A 2D array storing the coordinates of each point.
//         [[x1, y1], [x2, y2]...]
//
// Output:
// A 3D array storing the outlines of each Voronoi cell, ordered the same way as the input data.
// [[[x1, y1], [x2, y2]...],
//  [[x1, y1], [x2, y2]...]...]

export function voronoi(data) {
	let points = data.map((coord) => new Point(coord[0], coord[1]));

	BowyerWatson(points);

	let cells = points.map((p) => {
		return findVoronoiCell(p);
	});

	return cells;
}
