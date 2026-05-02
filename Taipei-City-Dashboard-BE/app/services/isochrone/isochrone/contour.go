package isochrone

import (
	"math"
)

// extractBoundary generates a smooth isochrone contour using:
// 1. Grid-based cost interpolation with KNN spatial index
// 2. Gaussian smoothing
// 3. Flood-fill for connected region identification
// 4. Marching squares on the smooth cost grid for contour extraction
func extractBoundary(
	adj [][]walkEdge,
	cost []float64,
	projX, projY []float64,
	threshold float64,
) [][][2]float64 {
	// --- 1. Find bounding box and query point ---
	var minX, minY, maxX, maxY float64
	minX, minY = math.Inf(1), math.Inf(1)
	maxX, maxY = math.Inf(-1), math.Inf(-1)

	queryX, queryY := 0.0, 0.0
	minCost := math.Inf(1)

	for i := range cost {
		if cost[i] > threshold || cost[i] < 0 {
			continue
		}
		if projX[i] == 0 && projY[i] == 0 {
			continue
		}
		if projX[i] < minX {
			minX = projX[i]
		}
		if projX[i] > maxX {
			maxX = projX[i]
		}
		if projY[i] < minY {
			minY = projY[i]
		}
		if projY[i] > maxY {
			maxY = projY[i]
		}
		if cost[i] < minCost {
			minCost = cost[i]
			queryX, queryY = projX[i], projY[i]
		}
	}

	if queryX == 0 {
		return nil
	}

	// --- 2. Create adaptive cost grid ---
	const padding = 2500.0
	const maxCells = 500

	minX -= padding
	minY -= padding
	maxX += padding
	maxY += padding

	bboxW := maxX - minX
	bboxH := maxY - minY
	cellSize := math.Max(bboxW, bboxH) / float64(maxCells)
	if cellSize < 200.0 {
		cellSize = 200.0
	}

	nx := int(bboxW/cellSize) + 1
	ny := int(bboxH/cellSize) + 1

	// Build spatial index (bins for KNN lookup)
	// Use coarser bins so each bin has more stops → fewer ring expansions needed
	binSize := cellSize * 8
	binNX := int(bboxW/binSize) + 2
	binNY := int(bboxH/binSize) + 2

	type stopInfo struct{ x, y, cost float64 }
	bins := make([][][]stopInfo, binNX)
	for i := range bins {
		bins[i] = make([][]stopInfo, binNY)
	}

	for i := range cost {
		if cost[i] > threshold || cost[i] < 0 {
			continue
		}
		if projX[i] == 0 && projY[i] == 0 {
			continue
		}
		s := stopInfo{projX[i], projY[i], cost[i]}
		bx := int((s.x - minX) / binSize)
		by := int((s.y - minY) / binSize)
		if bx >= 0 && bx < binNX && by >= 0 && by < binNY {
			bins[bx][by] = append(bins[bx][by], s)
		}
	}

	// Compute cost at each grid cell using K-nearest stops (expanding ring search).
	// Every cell is guaranteed to get a cost value, even in sparse areas.
	const knnK = 5
	maxExpand := binNX
	if binNY < maxExpand {
		maxExpand = binNY
	}

	grid := make([][]float64, nx)
	for ix := range grid {
		grid[ix] = make([]float64, ny)
	}

	for ix := 0; ix < nx; ix++ {
		cx := minX + float64(ix)*cellSize
		bxC := int((cx - minX) / binSize)
		for iy := 0; iy < ny; iy++ {
			cy := minY + float64(iy)*cellSize
			byC := int((cy - minY) / binSize)

			// Expanding ring: collect candidates until we have >= K stops
			var candidates []struct {
				dSq  float64
				cost float64
			}
			for ring := 0; ring <= maxExpand && len(candidates) < knnK; ring++ {
				for dbx := -ring; dbx <= ring; dbx++ {
					for dby := -ring; dby <= ring; dby++ {
						if ring > 0 && dbx > -ring && dbx < ring && dby > -ring && dby < ring {
							continue
						}
						obx := bxC + dbx
						oby := byC + dby
						if obx < 0 || obx >= binNX || oby < 0 || oby >= binNY {
							continue
						}
						for _, s := range bins[obx][oby] {
							dx := cx - s.x
							dy := cy - s.y
							candidates = append(candidates, struct {
								dSq  float64
								cost float64
							}{dx*dx + dy*dy, s.cost})
						}
					}
				}
			}

			// min(stop_cost + walk_time) among all candidates
			best := math.Inf(1)
			for _, c := range candidates {
				walkTime := math.Sqrt(c.dSq) / walkSpd
				adj := c.cost + walkTime
				if adj < best {
					best = adj
				}
			}
			grid[ix][iy] = best
		}
	}

	// --- 3. Gaussian blur ---
	sigma := math.Max(1.0, 50.0/cellSize)
	grid = gaussianBlur(grid, nx, ny, sigma)

	// --- 4. Flood-fill to find connected region (used as mask) ---
	inside := make([][]bool, nx)
	for ix := range inside {
		inside[ix] = make([]bool, ny)
		for iy := 0; iy < ny; iy++ {
			inside[ix][iy] = grid[ix][iy] < threshold
		}
	}

	qx := int((queryX - minX) / cellSize)
	qy := int((queryY - minY) / cellSize)
	if qx < 0 || qx >= nx || qy < 0 || qy >= ny || !inside[qx][qy] {
		return nil
	}

	// BFS flood-fill
	visited := make([][]bool, nx)
	for ix := range visited {
		visited[ix] = make([]bool, ny)
	}
	type cell struct{ x, y int }
	queue := []cell{{qx, qy}}
	visited[qx][qy] = true
	dx4 := [4]int{0, 1, 0, -1}
	dy4 := [4]int{1, 0, -1, 0}

	for len(queue) > 0 {
		c := queue[0]
		queue = queue[1:]
		for d := 0; d < 4; d++ {
			nbx := c.x + dx4[d]
			nby := c.y + dy4[d]
			if nbx < 0 || nbx >= nx || nby < 0 || nby >= ny {
				continue
			}
			if visited[nbx][nby] || !inside[nbx][nby] {
				continue
			}
			visited[nbx][nby] = true
			queue = append(queue, cell{nbx, nby})
		}
	}

	// Mask: cells NOT in the connected region get high cost (above threshold)
	highCost := threshold + 1e6
	for ix := 0; ix < nx; ix++ {
		for iy := 0; iy < ny; iy++ {
			if !visited[ix][iy] {
				grid[ix][iy] = highCost
			}
		}
	}

	// --- 5. Marching squares on masked smooth grid ---
	segments := marchingSquares(grid, minX, minY, cellSize, threshold)
	rings := stitchSegments(segments)

	if len(rings) == 0 {
		return nil
	}

	// Select ring containing query point (largest such ring)
	bestRing := -1
	bestLen := 0
	for i, ring := range rings {
		if pointInRing(queryX, queryY, ring) && len(ring) > bestLen {
			bestLen = len(ring)
			bestRing = i
		}
	}

	// Fallback: largest ring
	if bestRing == -1 {
		for i, ring := range rings {
			if len(ring) > bestLen {
				bestLen = len(ring)
				bestRing = i
			}
		}
	}

	if bestRing == -1 {
		return nil
	}

	rawRing := rings[bestRing]
	ring := douglasPeucker(rawRing, cellSize*0.15)
	if !pointInRing(queryX, queryY, ring) {
		ring = rawRing
	}

	// Ensure closed
	if len(ring) > 0 && (ring[0][0] != ring[len(ring)-1][0] || ring[0][1] != ring[len(ring)-1][1]) {
		ring = append(ring, ring[0])
	}

	return [][][2]float64{ring}
}

// extractContourFromGrid extracts a single contour polygon from a pre-computed
// flat cost grid. Coordinates in the returned ring are in grid-cell units
// (fractional indices). The grid is indexed as grid[ix*ny+iy].
func extractContourFromGrid(
	grid []float64, nx, ny int,
	qx, qy int,
	threshold float64,
) [][2]float64 {
	// BFS flood fill from query cell to find connected region.
	inside := make([]bool, nx*ny)
	for i, v := range grid {
		inside[i] = v < threshold
	}

	if qx < 0 || qx >= nx || qy < 0 || qy >= ny || !inside[qx*ny+qy] {
		return nil
	}

	visited := make([]bool, nx*ny)
	type cell struct{ x, y int }
	queue := []cell{{qx, qy}}
	visited[qx*ny+qy] = true
	dx4 := [4]int{0, 1, 0, -1}
	dy4 := [4]int{1, 0, -1, 0}

	for len(queue) > 0 {
		c := queue[0]
		queue = queue[1:]
		for d := 0; d < 4; d++ {
			nbx := c.x + dx4[d]
			nby := c.y + dy4[d]
			if nbx < 0 || nbx >= nx || nby < 0 || nby >= ny {
				continue
			}
			idx := nbx*ny + nby
			if visited[idx] || !inside[idx] {
				continue
			}
			visited[idx] = true
			queue = append(queue, cell{nbx, nby})
		}
	}

	// Mask disconnected cells.
	highCost := threshold + 1e6
	masked := make([]float64, nx*ny)
	copy(masked, grid)
	for i := range masked {
		if !visited[i] {
			masked[i] = highCost
		}
	}

	// Marching squares on the masked grid.
	segments := marchingSquaresFlat(masked, nx, ny, threshold)
	rings := stitchSegments(segments)

	if len(rings) == 0 {
		return nil
	}

	// Select the outer ring for the connected region containing the query
	// cell. Marching squares can also return hole rings; those must not become
	// the displayed isochrone.
	bestRing := -1
	bestLen := 0
	for i, ring := range rings {
		if pointInRing(float64(qx), float64(qy), ring) && len(ring) > bestLen {
			bestLen = len(ring)
			bestRing = i
		}
	}
	if bestRing == -1 {
		for i, ring := range rings {
			if len(ring) > bestLen {
				bestLen = len(ring)
				bestRing = i
			}
		}
	}

	queryX := float64(qx)
	queryY := float64(qy)
	rawRing := rings[bestRing]
	ring := douglasPeucker(rawRing, 0.5)
	if !pointInRing(queryX, queryY, ring) {
		ring = rawRing
	}

	// Chaikin smoothing (2 iterations for organic curves).
	smoothed := chaikinSmooth(ring, 2)
	if pointInRing(queryX, queryY, smoothed) {
		ring = smoothed
	}

	// Ensure closed.
	if len(ring) > 0 && (ring[0][0] != ring[len(ring)-1][0] || ring[0][1] != ring[len(ring)-1][1]) {
		ring = append(ring, ring[0])
	}

	return ring
}

func extractAllContoursFromGrid(
	grid []float64, nx, ny int,
	threshold float64,
) [][][2]float64 {
	segments := marchingSquaresFlat(grid, nx, ny, threshold)
	rings := stitchSegments(segments)
	if len(rings) == 0 {
		return nil
	}

	areas := make([]float64, len(rings))
	for i, ring := range rings {
		areas[i] = math.Abs(ringArea(ring))
	}

	result := make([][][2]float64, 0, len(rings))
	for i, rawRing := range rings {
		if len(rawRing) < 4 {
			continue
		}
		pt := rawRing[0]
		insideLarger := false
		for j, other := range rings {
			if i == j || areas[j] <= areas[i] {
				continue
			}
			if pointInRing(pt[0], pt[1], other) {
				insideLarger = true
				break
			}
		}
		if insideLarger {
			continue
		}

		ring := douglasPeucker(rawRing, 0.5)
		smoothed := chaikinSmooth(ring, 2)
		if len(smoothed) >= 4 {
			ring = smoothed
		}
		if len(ring) > 0 && (ring[0][0] != ring[len(ring)-1][0] || ring[0][1] != ring[len(ring)-1][1]) {
			ring = append(ring, ring[0])
		}
		result = append(result, ring)
	}

	return result
}

// marchingSquaresFlat extracts contour segments from a flat cost grid indexed
// as grid[ix*ny+iy]. Returns segments in grid-cell coordinates.
func marchingSquaresFlat(
	grid []float64, nx, ny int,
	threshold float64,
) [][2][2]float64 {
	var segments [][2][2]float64

	interpolate := func(v1, v2 float64) float64 {
		if v1 == v2 {
			return 0.5
		}
		t := (threshold - v1) / (v2 - v1)
		if t < 0 {
			t = 0
		}
		if t > 1 {
			t = 1
		}
		return t
	}

	for ix := 0; ix < nx-1; ix++ {
		for iy := 0; iy < ny-1; iy++ {
			v00 := grid[ix*ny+iy]
			v10 := grid[(ix+1)*ny+iy]
			v11 := grid[(ix+1)*ny+(iy+1)]
			v01 := grid[ix*ny+(iy+1)]

			if math.IsInf(v00, 1) || math.IsInf(v10, 1) || math.IsInf(v11, 1) || math.IsInf(v01, 1) {
				continue
			}

			ci := 0
			if v00 < threshold {
				ci |= 1
			}
			if v10 < threshold {
				ci |= 2
			}
			if v11 < threshold {
				ci |= 4
			}
			if v01 < threshold {
				ci |= 8
			}

			if ci == 0 || ci == 15 {
				continue
			}

			x := float64(ix)
			y := float64(iy)

			bottom := [2]float64{x + interpolate(v00, v10), y}
			right := [2]float64{x + 1, y + interpolate(v10, v11)}
			top := [2]float64{x + interpolate(v01, v11), y + 1}
			left := [2]float64{x, y + interpolate(v00, v01)}

			switch ci {
			case 1, 14:
				segments = append(segments, [2][2]float64{left, bottom})
			case 2, 13:
				segments = append(segments, [2][2]float64{bottom, right})
			case 3, 12:
				segments = append(segments, [2][2]float64{left, right})
			case 4, 11:
				segments = append(segments, [2][2]float64{right, top})
			case 5:
				segments = append(segments, [2][2]float64{left, bottom})
				segments = append(segments, [2][2]float64{right, top})
			case 6, 9:
				segments = append(segments, [2][2]float64{bottom, top})
			case 7, 8:
				segments = append(segments, [2][2]float64{left, top})
			case 10:
				segments = append(segments, [2][2]float64{bottom, right})
				segments = append(segments, [2][2]float64{left, top})
			}
		}
	}

	return segments
}

// normalizedGaussianBlurFlat applies separable Gaussian blur on a flat grid.
// Cells with inf cost are excluded from the kernel (weight=0). Cells where the
// effective kernel weight is below minWeight receive the penalty value.
func normalizedGaussianBlurFlat(
	grid []float64, nx, ny int,
	sigma float64,
	penalty float64,
) []float64 {
	if sigma <= 0 {
		return grid
	}

	radius := int(math.Ceil(sigma * 3))
	if radius < 1 {
		radius = 1
	}
	kSize := 2*radius + 1
	kernel := make([]float64, kSize)
	sum := 0.0
	for i := 0; i < kSize; i++ {
		x := float64(i - radius)
		kernel[i] = math.Exp(-x * x / (2 * sigma * sigma))
		sum += kernel[i]
	}
	for i := range kernel {
		kernel[i] /= sum
	}

	// X pass.
	temp := make([]float64, nx*ny)
	for ix := 0; ix < nx; ix++ {
		for iy := 0; iy < ny; iy++ {
			v, w := 0.0, 0.0
			for k := 0; k < kSize; k++ {
				sx := ix - radius + k
				if sx < 0 || sx >= nx {
					continue
				}
				val := grid[sx*ny+iy]
				if math.IsInf(val, 1) {
					continue
				}
				v += val * kernel[k]
				w += kernel[k]
			}
			if w > 1e-5 {
				temp[ix*ny+iy] = v / w
			} else {
				temp[ix*ny+iy] = math.Inf(1)
			}
		}
	}

	// Y pass.
	result := make([]float64, nx*ny)
	for ix := 0; ix < nx; ix++ {
		for iy := 0; iy < ny; iy++ {
			v, w := 0.0, 0.0
			for k := 0; k < kSize; k++ {
				sy := iy - radius + k
				if sy < 0 || sy >= ny {
					continue
				}
				val := temp[ix*ny+sy]
				if math.IsInf(val, 1) {
					continue
				}
				v += val * kernel[k]
				w += kernel[k]
			}
			if w > 1e-5 {
				result[ix*ny+iy] = v / w
			} else {
				result[ix*ny+iy] = penalty
			}
		}
	}

	return result
}

// chaikinSmooth applies Chaikin corner-cutting smoothing to a ring.
// The ring must be closed (first point == last point).
func chaikinSmooth(ring [][2]float64, iterations int) [][2]float64 {
	if len(ring) <= 3 {
		return ring
	}

	result := make([][2]float64, len(ring))
	copy(result, ring)

	for it := 0; it < iterations; it++ {
		// Strip closing point if present.
		n := len(result)
		closed := n > 1 && result[0][0] == result[n-1][0] && result[0][1] == result[n-1][1]
		src := result
		if closed {
			src = result[:n-1]
		}

		var new [][2]float64
		for i := 0; i < len(src); i++ {
			j := (i + 1) % len(src)
			p0 := src[i]
			p1 := src[j]
			new = append(new,
				[2]float64{0.75*p0[0] + 0.25*p1[0], 0.75*p0[1] + 0.25*p1[1]},
				[2]float64{0.25*p0[0] + 0.75*p1[0], 0.25*p0[1] + 0.75*p1[1]},
			)
		}

		// Re-close.
		if closed {
			new = append(new, new[0])
		}
		result = new
	}

	return result
}

// marchingSquares extracts contour segments from a smooth cost grid.
func marchingSquares(
	grid [][]float64,
	minX, minY, cellSize float64,
	threshold float64,
) [][2][2]float64 {
	nx := len(grid)
	ny := len(grid[0])

	var segments [][2][2]float64

	interpolate := func(v1, v2 float64) float64 {
		if v1 == v2 {
			return 0.5
		}
		t := (threshold - v1) / (v2 - v1)
		if t < 0 {
			t = 0
		}
		if t > 1 {
			t = 1
		}
		return t
	}

	for ix := 0; ix < nx-1; ix++ {
		for iy := 0; iy < ny-1; iy++ {
			v00 := grid[ix][iy]
			v10 := grid[ix+1][iy]
			v11 := grid[ix+1][iy+1]
			v01 := grid[ix][iy+1]

			if math.IsInf(v00, 1) || math.IsInf(v10, 1) || math.IsInf(v11, 1) || math.IsInf(v01, 1) {
				continue
			}

			ci := 0
			if v00 < threshold {
				ci |= 1
			}
			if v10 < threshold {
				ci |= 2
			}
			if v11 < threshold {
				ci |= 4
			}
			if v01 < threshold {
				ci |= 8
			}

			if ci == 0 || ci == 15 {
				continue
			}

			x := minX + float64(ix)*cellSize
			y := minY + float64(iy)*cellSize

			bottom := [2]float64{x + cellSize*interpolate(v00, v10), y}
			right := [2]float64{x + cellSize, y + cellSize*interpolate(v10, v11)}
			top := [2]float64{x + cellSize*interpolate(v01, v11), y + cellSize}
			left := [2]float64{x, y + cellSize*interpolate(v00, v01)}

			switch ci {
			case 1, 14:
				segments = append(segments, [2][2]float64{left, bottom})
			case 2, 13:
				segments = append(segments, [2][2]float64{bottom, right})
			case 3, 12:
				segments = append(segments, [2][2]float64{left, right})
			case 4, 11:
				segments = append(segments, [2][2]float64{right, top})
			case 5:
				segments = append(segments, [2][2]float64{left, bottom})
				segments = append(segments, [2][2]float64{right, top})
			case 6, 9:
				segments = append(segments, [2][2]float64{bottom, top})
			case 7, 8:
				segments = append(segments, [2][2]float64{left, top})
			case 10:
				segments = append(segments, [2][2]float64{bottom, right})
				segments = append(segments, [2][2]float64{left, top})
			}
		}
	}

	return segments
}

// stitchSegments connects line segments into closed rings.
// Endpoints from marchingSquaresFlat are deterministic, so exact equality
// is used as the map key rather than tolerance-based matching.
func stitchSegments(segments [][2][2]float64) [][][2]float64 {
	if len(segments) == 0 {
		return nil
	}

	type halfEdge struct{ segIdx, otherEnd int }
	// adj maps each endpoint to the half-edges that leave it.
	adj := make(map[[2]float64][]halfEdge, 2*len(segments))
	for i, seg := range segments {
		adj[seg[0]] = append(adj[seg[0]], halfEdge{i, 1})
		adj[seg[1]] = append(adj[seg[1]], halfEdge{i, 0})
	}

	used := make([]bool, len(segments))
	var rings [][][2]float64

	for i, seg := range segments {
		if used[i] {
			continue
		}
		used[i] = true
		start := seg[0]
		ring := [][2]float64{start, seg[1]}
		cur := seg[1]
		closed := false

		for !closed {
			found := false
			for _, he := range adj[cur] {
				if used[he.segIdx] {
					continue
				}
				used[he.segIdx] = true
				dest := segments[he.segIdx][he.otherEnd]
				if dest == start && len(ring) >= 3 {
					ring = append(ring, start)
					closed = true
				} else {
					ring = append(ring, dest)
					cur = dest
				}
				found = true
				break
			}
			if !found {
				break
			}
		}

		if closed && len(ring) >= 4 {
			rings = append(rings, ring)
		}
	}

	return rings
}

// pointInRing tests if point (px, py) is inside a closed ring using ray casting.
func pointInRing(px, py float64, ring [][2]float64) bool {
	n := len(ring)
	if n < 4 {
		return false
	}
	inside := false
	j := n - 2
	for i := 0; i < n-1; i++ {
		yi := ring[i][1]
		yj := ring[j][1]
		if (yi > py) != (yj > py) {
			xi := ring[i][0]
			xj := ring[j][0]
			if px < (xj-xi)*(py-yi)/(yj-yi)+xi {
				inside = !inside
			}
		}
		j = i
	}
	return inside
}

func ringArea(ring [][2]float64) float64 {
	if len(ring) < 3 {
		return 0
	}
	area := 0.0
	for i := 0; i < len(ring)-1; i++ {
		area += ring[i][0]*ring[i+1][1] - ring[i+1][0]*ring[i][1]
	}
	return area / 2
}

// douglasPeucker simplifies a ring.
func douglasPeucker(ring [][2]float64, epsilon float64) [][2]float64 {
	if len(ring) <= 3 {
		return ring
	}
	n := len(ring) - 1
	maxDist := 0.0
	maxIdx := 0
	for i := 1; i < n; i++ {
		d := pointLineDist(ring[i], ring[0], ring[n])
		if d > maxDist {
			maxDist = d
			maxIdx = i
		}
	}
	if maxDist > epsilon {
		left := douglasPeucker(ring[:maxIdx+1], epsilon)
		right := douglasPeucker(ring[maxIdx:], epsilon)
		return append(left[:len(left)-1], right...)
	}
	return [][2]float64{ring[0], ring[n]}
}

func pointLineDist(p, a, b [2]float64) float64 {
	dx := b[0] - a[0]
	dy := b[1] - a[1]
	dSq := dx*dx + dy*dy
	if dSq == 0 {
		return math.Sqrt((p[0]-a[0])*(p[0]-a[0]) + (p[1]-a[1])*(p[1]-a[1]))
	}
	t := ((p[0]-a[0])*dx + (p[1]-a[1])*dy) / dSq
	if t < 0 {
		t = 0
	}
	if t > 1 {
		t = 1
	}
	projX := a[0] + t*dx
	projY := a[1] + t*dy
	return math.Sqrt((p[0]-projX)*(p[0]-projX) + (p[1]-projY)*(p[1]-projY))
}

// gaussianBlur applies separable Gaussian blur.
func gaussianBlur(grid [][]float64, nx, ny int, sigma float64) [][]float64 {
	if sigma <= 0 {
		return grid
	}

	radius := int(math.Ceil(sigma * 3))
	if radius < 1 {
		radius = 1
	}
	kSize := 2*radius + 1
	kernel := make([]float64, kSize)
	sum := 0.0
	for i := 0; i < kSize; i++ {
		x := float64(i - radius)
		kernel[i] = math.Exp(-x * x / (2 * sigma * sigma))
		sum += kernel[i]
	}
	for i := range kernel {
		kernel[i] /= sum
	}

	temp := make([][]float64, nx)
	for ix := range temp {
		temp[ix] = make([]float64, ny)
		for iy := 0; iy < ny; iy++ {
			v, w := 0.0, 0.0
			for k := 0; k < kSize; k++ {
				sx := ix - radius + k
				if sx < 0 || sx >= nx {
					continue
				}
				if math.IsInf(grid[sx][iy], 1) {
					continue
				}
				v += grid[sx][iy] * kernel[k]
				w += kernel[k]
			}
			if w > 0 {
				temp[ix][iy] = v / w
			} else {
				temp[ix][iy] = math.Inf(1)
			}
		}
	}

	result := make([][]float64, nx)
	for ix := range result {
		result[ix] = make([]float64, ny)
		for iy := 0; iy < ny; iy++ {
			v, w := 0.0, 0.0
			for k := 0; k < kSize; k++ {
				sy := iy - radius + k
				if sy < 0 || sy >= ny {
					continue
				}
				if math.IsInf(temp[ix][sy], 1) {
					continue
				}
				v += temp[ix][sy] * kernel[k]
				w += kernel[k]
			}
			if w > 0 {
				result[ix][iy] = v / w
			} else {
				result[ix][iy] = math.Inf(1)
			}
		}
	}

	return result
}
