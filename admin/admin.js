'use strict';
(async () => {
  const status = document.querySelector('#publish-status');
  const refresh = document.querySelector('#refresh');
  const repository = 'RenatusPang/miaomeihuamu';
  let branch = 'codex/owner-cms-20261104';
  let release;
  try {
    const response = await fetch(`./release.json?check=${Date.now()}`, { cache: 'no-store' });
    if (response.ok) release = await response.json();
    if (release?.repository === repository && typeof release.branch === 'string') branch = release.branch;
  } catch { /* Local source preview has no packaged release yet. */ }
  document.querySelector('#branch').textContent = branch;
  const test = branch !== 'main';
  document.querySelector('#scope').textContent = test ? '独立测试分支。保存只生成预览，不更新正式官网。' : '正式内容分支。保存后需等待生成与发布成功。';
  document.querySelector('#cms').href = `https://app.pagescms.org/${repository}/${encodeURIComponent(branch)}`;
  document.querySelector('#history').href = `https://github.com/${repository}/commits/${encodeURIComponent(branch)}/content`;
  document.querySelector('#runs').href = `https://github.com/${repository}/actions/workflows/cms-site.yml?query=branch%3A${encodeURIComponent(branch)}`;
  document.querySelector('#version').textContent = release ? release.revision.slice(0, 12) : '当前本地工作副本';
  async function check() {
    refresh.disabled = true;
    status.textContent = '正在读取保存与生成状态…';
    try {
      const currentRelease = await fetch(`./release.json?check=${Date.now()}`, { cache: 'no-store' });
      if (currentRelease.ok) {
        const current = await currentRelease.json();
        if (current.repository === repository && current.branch === branch) {
          release = current;
          document.querySelector('#version').textContent = release.revision.slice(0, 12);
        }
      }
      const endpoint = `https://api.github.com/repos/${repository}`;
      const response = await fetch(`${endpoint}/commits/${encodeURIComponent(branch)}`);
      if (!response.ok) throw Error('版本状态暂不可读');
      const commit = await response.json();
      const jobs = await fetch(`${endpoint}/actions/workflows/cms-site.yml/runs?branch=${encodeURIComponent(branch)}&per_page=10`);
      if (!jobs.ok) throw Error('生成记录暂不可读');
      const data = await jobs.json();
      const run = data.workflow_runs.find(item => item.head_sha === commit.sha);
      let message = `已保存版本 ${commit.sha.slice(0, 8)}。`;
      if (!run) message += '暂未发现对应生成记录，请打开生成记录确认。';
      else if (run.status !== 'completed') message += '正在等待或执行生成。';
      else if (run.conclusion !== 'success') message += `生成未成功（${run.conclusion}），请查看错误并修正内容。`;
      else if (test) message += '测试预览文件已生成；未发布到正式官网。';
      else if (location.origin === 'https://miaomeihuamu.com' && release?.revision === commit.sha && release.preview === false) {
        message += '正式官网已提供此版本，可打开页面核对内容。';
      } else {
        message += '生成流程已完成，当前页面尚未确认正式发布到此版本。请查看 deploy 发布步骤和官网版本。';
      }
      status.textContent = message;
    } catch (error) {
      status.textContent = `${error.message}。也可能达到 GitHub 公开查询频率限制，请用下方“生成记录”核对。`;
    } finally { refresh.disabled = false; }
  }
  refresh.addEventListener('click', check);
})();
