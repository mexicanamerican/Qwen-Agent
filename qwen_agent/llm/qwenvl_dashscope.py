import os
from http import HTTPStatus
from typing import Dict, Iterator, List, Optional

import dashscope

from qwen_agent.llm.base import BaseChatModel, ModelServiceError


class QwenVLChatAtDS(BaseChatModel):

    def __init__(self, cfg: Optional[Dict] = None):
        super().__init__(cfg)
        self.model = self.cfg.get('model', 'qwen-vl-plus')
        dashscope.api_key = os.getenv('DASHSCOPE_API_KEY',
                                      default=self.cfg.get('api_key', ''))
        assert dashscope.api_key, 'DASHSCOPE_API_KEY is required.'

    def _chat_stream(
        self,
        messages: List[Dict],
        delta_stream: bool = False,
    ) -> Iterator[List[Dict]]:
        if delta_stream:
            raise NotImplementedError
        response = dashscope.MultiModalConversation.call(
            model=self.model,
            messages=messages,
            result_format='message',
            stream=True,
            **self.generate_cfg)

        for trunk in response:
            if trunk.status_code == HTTPStatus.OK:
                yield [trunk.output.choices[0].message]
            else:
                err = '\nError code: %s. Error message: %s' % (trunk.code,
                                                               trunk.message)
                raise ModelServiceError(err)

    def _chat_no_stream(
        self,
        messages: List[Dict],
    ) -> List[Dict]:
        response = dashscope.MultiModalConversation.call(
            model=self.model,
            messages=messages,
            result_format='message',
            stream=False,
            **self.generate_cfg)
        if response.status_code == HTTPStatus.OK:
            return [response.output.choices[0].message]
        else:
            err = 'Error code: %s, error message: %s' % (
                response.code,
                response.message,
            )
            raise ModelServiceError(err)

    def _format_msg_for_llm(self, messages: List[Dict]) -> List[Dict]:
        return messages