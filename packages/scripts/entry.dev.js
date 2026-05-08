		// 运行脚本
		start({
			projects: projects,
			renderConfig: {
				renderScript: RenderScript,
				styles: [GM_getResourceText('STYLE')],
				defaultPanelName: CommonProject.scripts.guide.namespace,
				title: `OCS DEV-${infos.script.version}`
			},
			updatePage: 'https://docs.ocsjs.com/docs/update'
		});
	})();
}
