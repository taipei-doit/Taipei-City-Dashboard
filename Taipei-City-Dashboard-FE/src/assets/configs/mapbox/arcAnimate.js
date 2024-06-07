import { ArcLayer } from "@deck.gl/layers";

const defaultProps = {
	coef: { type: "number", value: 0 },
};

export class AnimatedArcLayer extends ArcLayer {
	static layerName = "AnimatedArcLayer";
	static defaultProps = defaultProps;

	getShaders() {
		return Object.assign({}, super.getShaders(), {
			inject: {
				"vs:#decl": `
                    uniform float coef;
                `,
				"vs:#main-end": `
                    if (coef > 0.0) {
                        vec4 pct = vec4(segmentRatio);
                        pct.a = step(coef, segmentRatio);
                        vec4 colorC = instanceSourceColors;
						vec4 colorA = instanceTargetColors;
                        vec4 colorB = vec4(vec3(instanceTargetColors),0.0);
						vec4 baseColor = mix(colorC, colorA, segmentRatio);
						vec4 color = mix(baseColor, colorB, pct.a);
                        vColor = color;
                        DECKGL_FILTER_COLOR(vColor, geometry);
                    }
                `,
			},
		});
	}

	draw(opts) {
		this.state.model.setUniforms({
			coef: this.props.coef,
		});
		super.draw(opts);
	}
}
