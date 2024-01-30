export const validateEmail = (rule, value, callback) => {
	if (value === "") {
		callback(new Error("請輸入E-mail"));
	}
	const re =
		/^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
	if (re.test(String(value).toLowerCase())) {
		callback();
	} else {
		callback(new Error("請輸入E-mail正確格式"));
	}
};
export const validatePass = (rule, value, callback) => {
	if (value === "") {
		callback(new Error("請輸入密碼"));
	}
	const re = /^(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{6,30}$/;
	if (re.test(String(value))) {
		callback();
	} else {
		callback(
			new Error(
				"至少有一個數字，一個小寫英文字母，一個大寫英文字母，字串長度在 6 ~ 30 個字母之間"
			)
		);
	}
};
export const validateText = (rule, value, callback) => {
	if (value === "") {
		callback(new Error("請輸入密碼"));
	}
	callback();
};

export const validateStrInput = (input) => {
	if (input && input.length > 20) {
		return "格式不正確，數入字數過多";
	} else {
		const Reg =
			/[\u4e00-\u9fa5_a-zA-Z0-9]|(\u00a9|\u00ae|[\u2000-\u3300]|\ud83c[\ud000-\udfff]|\ud83d[\ud000-\udfff]|\ud83e[\ud000-\udfff])/;
		const result = RegExp(Reg).test(input);
		const strSplit = input.split("");
		if (result && !(strSplit.includes("<") && strSplit.includes(">")))
			return true;
		return "格式不正確，僅允許輸入中英文";
	}
};

export const validateEngInput = (input) => {
	if (input && input.length > 20) {
		return "格式不正確，數入字數過多";
	} else {
		const Reg = /^[-_a-z0-9]*$/i;
		const result = RegExp(Reg).test(input);
		const strSplit = input.split("");
		if (result && !(strSplit.includes("<") && strSplit.includes(">")))
			return true;
		return "格式不正確，僅允許輸入英文";
	}
};
