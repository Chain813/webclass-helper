		// 运行脚本
		start({
			projects: projects,
			renderConfig: {
				renderScript: RenderScript,
				styles: [STYLE],
				defaultPanelName: CommonProject.scripts.guide.namespace,
				title: `OCS-${infos.script.version}`
			},
			updatePage: 'https://docs.ocsjs.com/docs/update'
		});
	})();
}
