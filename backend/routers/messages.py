from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from database import AsyncSessionLocal
from models.models import Message, User, LineGroup
from schemas import MessageResponse, MessageReply, MessageSend
from deps import get_db, get_current_user, require_role
from services.line_service import line_service

router = APIRouter(prefix="/api/messages", tags=["messages"])

@router.get("/", response_model=List[MessageResponse])
async def list_messages(
    farm_id: Optional[int] = None,
    limit: int = 30,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 獲取訊息列表 (Get message list)
    query = select(Message)
    
    if current_user.role == "leader":
        if not current_user.farm_id:
            return []
        query = query.where(Message.farm_id == current_user.farm_id)
    elif farm_id:
        query = query.where(Message.farm_id == farm_id)
        
    result = await db.execute(query.order_by(Message.created_at.desc()).limit(limit).offset(offset))
    return result.scalars().all()

@router.get("/{msg_id}", response_model=MessageResponse)
async def get_message(
    msg_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 獲取單一訊息 (Get single message)
    result = await db.execute(select(Message).where(Message.id == msg_id))
    msg = result.scalar_one_or_none()
    
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
        
    if current_user.role == "leader" and msg.farm_id != current_user.farm_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this message")
        
    return msg

@router.post("/reply")
async def reply_message(
    reply: MessageReply,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["boss", "supervisor"]))
):
    # 回覆訊息 (Reply to message)
    result = await db.execute(select(Message).where(Message.id == reply.reply_to_id))
    original_msg = result.scalar_one_or_none()
    
    if not original_msg or not original_msg.line_group_id:
        raise HTTPException(status_code=400, detail="Cannot reply to this message")
        
    # Send via LINE
    line_service.send_text_message(original_msg.line_group_id, reply.content)
    
    # Save reply
    new_msg = Message(
        line_group_id=original_msg.line_group_id,
        farm_id=original_msg.farm_id,
        content=reply.content,
        message_type="text",
        is_reply=True,
        reply_to_id=original_msg.id,
        replied_by=current_user.id
    )
    db.add(new_msg)
    await db.commit()
    return {"status": "success"}

@router.post("/send")
async def send_message(
    send: MessageSend,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["boss", "supervisor"]))
):
    # 發送新訊息 (Send new message)
    result = await db.execute(select(LineGroup).where(LineGroup.farm_id == send.farm_id))
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(status_code=400, detail="No LINE group linked to this farm")
        
    line_service.send_text_message(group.line_group_id, send.content)
    
    new_msg = Message(
        line_group_id=group.line_group_id,
        farm_id=send.farm_id,
        content=send.content,
        message_type="text",
        is_reply=True,
        replied_by=current_user.id
    )
    db.add(new_msg)
    await db.commit()
    return {"status": "success"}
