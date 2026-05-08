		// 运行脚本
		start({
			projects: projects,
			renderConfig: {
				renderScript: RenderScript,
				styles: [STYLE],
				defaultPanelName: CommonProject.scripts.guide.namespace,
				title: `OCS-全域名通用版-${infos.script.version}`
			},
			updatePage:
				GM_info.scriptHandler === 'Tampermonkey'
					? 'https://greasyfork.org/zh-CN/scripts/481438'
					: 'https://scriptcat.org/zh-CN/script-show-page/1398'
		});
	})();
}
